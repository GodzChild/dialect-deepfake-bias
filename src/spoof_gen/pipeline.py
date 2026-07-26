"""
Spoof Generation Pipeline
==========================
Orchestrates the generation of spoofed audio for all speakers
across all TTS/VC systems, and saves a full manifest for evaluation.

Output structure:
  data/generated_spoofs/
    ├── xtts_v2/
    │   ├── spk001_utt04_spoofed.wav
    │   ├── spk001_utt05_spoofed.wav
    │   └── ...
    ├── openvoice_v2/
    │   └── ...
    └── manifest.jsonl    # Complete record of all generations
"""

import json
import random
from dataclasses import asdict
from pathlib import Path

import jsonlines
import yaml
from tqdm import tqdm

from ..data.decte_loader import DECTELoader, Utterance
from .base import BaseSpoofGenerator, SpoofResult
from .xtts_gen import XTTSGenerator


def load_config(config_path: str) -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def create_generators(config: dict) -> list[BaseSpoofGenerator]:
    """Instantiate all enabled spoof generators from config."""
    generators = []
    output_dir = config["paths"]["output_dir"]
    gen_configs = config["generators"]

    if gen_configs["xtts_v2"]["enabled"]:
        cfg = gen_configs["xtts_v2"]
        generators.append(XTTSGenerator(
            output_dir=output_dir,
            model_name=cfg["model_name"],
            device=cfg["device"],
            target_sr=config["audio"]["target_sr"],
        ))

    if gen_configs.get("openvoice_v2", {}).get("enabled", False):
        # Deferred import: OpenVoice deps only exist in the `openvoice` env.
        from .openvoice_gen import OpenVoiceGenerator
        cfg = gen_configs["openvoice_v2"]
        generators.append(OpenVoiceGenerator(
            output_dir=output_dir,
            converter_ckpt_dir=cfg["converter_ckpt_dir"],
            base_speaker_ses_path=cfg["base_speaker_ses_path"],
            melo_language=cfg.get("melo_language", "EN"),
            melo_speaker_key=cfg.get("melo_speaker_key", "EN-Newest"),
            device=cfg.get("device", "cuda"),
            target_sr=config["audio"]["target_sr"],
        ))

    # Add other generators here as you enable them:
    # if gen_configs["styletts2"]["enabled"]:
    #     generators.append(StyleTTS2Generator(...))

    return generators


class SpoofPipeline:
    """
    Main pipeline: for each DECTE speaker, generate spoofed versions
    of their utterances using all enabled TTS/VC systems.
    """

    def __init__(self, config_path: str):
        self.config = load_config(config_path)
        self.generators = create_generators(self.config)
        self.manifest_path = Path(self.config["paths"]["output_dir"]) / "manifest.jsonl"
        self.results: list[SpoofResult] = []

        # Loader dispatch: default 'decte' preserves prior behaviour.
        # Set `loader: vctk` in a config (see configs/spoof_gen.vctk.test.yaml)
        # to swap in the VCTK control-set loader without touching DECTE code.
        paths = self.config["paths"]
        audio_cfg = self.config["audio"]
        loader_kind = str(self.config.get("loader", "decte")).lower()
        if loader_kind == "vctk":
            # Deferred import so DECTE-only runs never touch VCTK code.
            from ..data.vctk_loader import VCTKLoader
            vctk_cfg = self.config.get("vctk", {})
            self.loader = VCTKLoader(
                audio_dir=paths["vctk_audio_dir"],
                transcripts_dir=paths["vctk_transcripts_dir"],
                speaker_info_path=paths["vctk_speaker_info"],
                accent_filter=vctk_cfg.get("accent_filter", "English"),
                target_sr=audio_cfg["target_sr"],
                min_duration=audio_cfg["min_duration_sec"],
                max_duration=audio_cfg["max_duration_sec"],
            )
        else:
            self.loader = DECTELoader(
                audio_dir=paths["decte_audio_dir"],
                metadata_path=paths["decte_metadata"],
                transcripts_dir=paths["decte_transcripts_dir"],
                target_sr=audio_cfg["target_sr"],
                min_duration=audio_cfg["min_duration_sec"],
                max_duration=audio_cfg["max_duration_sec"],
            )

    def prepare_data(self):
        """Load and prepare DECTE corpus."""
        print("=" * 60)
        print("PREPARING DECTE DATA")
        print("=" * 60)
        self.loader.load_speaker_metadata()
        self.loader.discover_audio_files()
        self.loader.build_utterance_list()

    def run(self):
        """Run the full spoof generation pipeline."""
        self.prepare_data()

        protocol = self.config["protocol"]
        max_utts = protocol["max_utterances_per_speaker"]
        n_ref = protocol["reference_utterance_count"]
        seed = protocol["seed"]
        random.seed(seed)

        speakers_with_utts = set(u.speaker_id for u in self.loader.utterances)
        speaker_list = sorted(speakers_with_utts)
        max_speakers = protocol.get("max_speakers")
        if max_speakers:
            # Small-test mode: keep only speakers with enough valid utterances
            # to fill the full reference + target budget, so the run yields
            # exactly max_speakers * max_utts attempts.
            from collections import Counter
            utt_counts = Counter(u.speaker_id for u in self.loader.utterances)
            min_needed = n_ref + max_utts
            speaker_list = [s for s in speaker_list if utt_counts[s] >= min_needed]
            speaker_list = speaker_list[:max_speakers]

        print(f"\n{'=' * 60}")
        print(f"GENERATING SPOOFS")
        print(f"Speakers: {len(speaker_list)} (of {len(speakers_with_utts)} available)")
        print(f"Generators: {[g.name for g in self.generators]}")
        print(f"Max utterances per speaker: {max_utts}")
        print(f"{'=' * 60}\n")

        # Load all generator models
        for gen in self.generators:
            gen.load_model()

        # Process each speaker
        for spk_id in tqdm(speaker_list, desc="Speakers"):
            ref_utts, target_utts = self.loader.get_reference_and_target_utterances(
                spk_id, n_reference=n_ref
            )

            if not ref_utts or not target_utts:
                print(f"  Skipping {spk_id}: insufficient utterances")
                continue

            # Limit target utterances
            if len(target_utts) > max_utts:
                target_utts = random.sample(target_utts, max_utts)

            # Reference audio paths for voice cloning
            ref_paths = [u.audio_path for u in ref_utts]

            # Generate spoofs with each system
            for gen in self.generators:
                for utt in target_utts:
                    output_filename = f"{utt.utterance_id}_spoofed.wav"
                    output_path = str(gen.output_dir / output_filename)

                    # Skip if already generated (resume capability)
                    if Path(output_path).exists():
                        continue

                    result = gen.generate(
                        text=utt.transcript,
                        reference_audio_paths=ref_paths,
                        output_path=output_path,
                        language="en",
                    )
                    result.source_speaker_id = spk_id

                    self.results.append(result)

                    if not result.success:
                        tqdm.write(
                            f"  FAILED: {spk_id}/{utt.utterance_id} "
                            f"with {gen.name}: {result.error_message}"
                        )

        # Cleanup
        for gen in self.generators:
            gen.cleanup()

        # Save manifest
        self._save_manifest()
        self._print_summary()

    def _save_manifest(self):
        """Save complete generation manifest as JSONL.

        Merges with any existing manifest.jsonl so that entries generated
        in prior runs (whose files were skipped by the resume/skip logic
        above and are therefore absent from self.results) are preserved.
        Deduplication key: output_path. Newest entry wins.
        """
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing manifest (if any) keyed by output_path
        merged: dict[str, dict] = {}
        if self.manifest_path.exists():
            with jsonlines.open(str(self.manifest_path), mode="r") as reader:
                for record in reader:
                    key = record.get("output_path")
                    if key:
                        merged[key] = record

        # Overlay this run's results (newest wins on collision)
        for result in self.results:
            record = asdict(result)
            if result.source_speaker_id in self.loader.speakers:
                spk = self.loader.speakers[result.source_speaker_id]
                record["speaker_gender"] = spk.gender
                record["speaker_age_group"] = spk.age_group
                record["speaker_ses_class"] = spk.ses_class
                record["speaker_recording_era"] = spk.recording_era
            merged[record["output_path"]] = record

        # Rewrite merged set
        with jsonlines.open(str(self.manifest_path), mode="w") as writer:
            for record in merged.values():
                writer.write(record)

        print(f"\nManifest saved to {self.manifest_path} ({len(merged)} entries)")

    def _print_summary(self):
        """Print generation summary statistics."""
        total = len(self.results)
        success = sum(1 for r in self.results if r.success)
        failed = total - success

        print(f"\n{'=' * 60}")
        print(f"GENERATION SUMMARY")
        print(f"{'=' * 60}")
        print(f"Total attempts: {total}")
        print(f"Successful: {success} ({100*success/max(total,1):.1f}%)")
        print(f"Failed: {failed}")

        # Per-generator breakdown
        from collections import Counter
        gen_counts = Counter()
        gen_success = Counter()
        for r in self.results:
            gen_counts[r.generator_name] += 1
            if r.success:
                gen_success[r.generator_name] += 1

        for gen_name in sorted(gen_counts.keys()):
            total_g = gen_counts[gen_name]
            succ_g = gen_success[gen_name]
            print(f"  {gen_name}: {succ_g}/{total_g} successful")

        # Per social-variable breakdown
        print(f"\nPer gender:")
        gender_counts = Counter()
        for r in self.results:
            if r.success and r.source_speaker_id in self.loader.speakers:
                g = self.loader.speakers[r.source_speaker_id].gender
                gender_counts[g] += 1
        for g, c in sorted(gender_counts.items()):
            print(f"  {g}: {c} spoofed utterances")
