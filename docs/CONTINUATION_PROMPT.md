# Claude Continuation Prompt

**Copy everything between the `---` markers below and paste as your first message
in a new Claude conversation. This gives Claude full context without re-explaining.**

---

## PROJECT CONTEXT (read this first, don't respond to it yet — wait for my question)

I'm Calvin Oluyemi, MSc student at the Institute of Computational Perception, JKU Linz.
My thesis: "Does Your Accent Make You Vulnerable? Quantifying Dialect Bias in Audio
Deepfake Detection on Tyneside English."

**What I'm doing:** Testing whether audio deepfake detectors (AASIST, Wav2Vec2-AASIST,
Whisper-based) perform worse on dialectal speech (Tyneside English from the DECTE corpus)
vs standard-accent English (VCTK). I generate spoofed versions of DECTE speakers using
XTTS v2, OpenVoice, StyleTTS 2, and RVC, then measure detection EER/AUC per speaker group
(gender, age, SES). If bias exists, I mitigate it via accent-adversarial training
(gradient reversal layer).

**Why this matters:** Serditova & Tang (Interspeech 2025, arxiv 2603.24549) showed ASR
systems fail more on DECTE speakers — phonological dialect features cause systematic
transcription errors, patterned by gender/age/SES. My thesis asks: do deepfake *detectors*
have the same bias? If so, dialect speakers are doubly vulnerable — harder for AI to
understand AND harder for AI to protect from voice scams.

**Key relationships:**
- Prof. Karen Corrigan (Newcastle) gave me DECTE access and wants to see findings
  for possible collaboration. She suggested a "different approach" from Serditova & Tang.
- My JKU supervisor wants conference-worthy novelty.
- DECTE is non-commercial/academic use only (CC licence, copyrighted by Corrigan et al.).

**Project structure:**
```
dialect-deepfake-bias/
├── configs/spoof_gen.yaml       # TTS system configs
├── src/data/decte_loader.py     # DECTE corpus loader
├── src/spoof_gen/
│   ├── base.py                  # Abstract generator interface
│   ├── xtts_gen.py              # XTTS v2 voice cloning
│   └── pipeline.py              # Orchestration + manifest
├── scripts/
│   ├── 01_prepare_decte.py      # Data inspection
│   └── 02_generate_spoofs.py    # Main spoof generation
```

**Phase plan:**
- Phase 1 (now): Spoof generation pipeline — XTTS v2 first, then add others
- Phase 2: Run detectors + compute EER/AUC per speaker group
- Phase 3: Accent-adversarial AASIST mitigation
- Phase 4: Thesis + conference paper
- Deadline: October 2026

**My existing assets:**
- Whisper transcriptions of DECTE audio (text files matching audio filenames)
- Some previous AASIST training code from earlier repo (auralguard-aasistpp)
- DECTE audio downloaded and accessible

**Current status:** [UPDATE THIS EACH SESSION, e.g.: "Phase 1 — XTTS generation
running, 60/160 speakers processed, some failures on short utterances"]

---

Now here's my current question: [YOUR QUESTION HERE]
