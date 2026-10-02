# Project notes

This repository grew alongside the thesis, so it is not organised like a finished software package.

The early work focused on preparing DECTE and getting XTTS generation working. Later experiments added VCTK, OpenVoice v2, bootstrap confidence intervals, a second detector and the mitigation study. This is why some of the later analysis lives in numbered scripts instead of reusable modules.

A few practical choices are worth keeping in mind:

- DECTE data is not included in the repository.
- generated audio and result folders are ignored because they are large and reproducible;
- AASIST training and the mitigation fine-tuning were done in the separate `auralguard-aasistpp` project;
- XTTS and OpenVoice were kept in separate environments because of dependency conflicts;
- the thesis interpretation changed during the work: the final result is not a simple "dialect always performs worse" story, because OpenVoice reverses the DECTE/VCTK direction.

For the final numbers and their limitations, use `THESIS_FINDINGS_LOG.md` rather than older planning documents.
