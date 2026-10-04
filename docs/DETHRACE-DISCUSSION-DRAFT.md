# Dethrace Discussion draft — Carmageddon Dethrace Modernizer

Suggested title:

**Community project: Carmageddon Dethrace Modernizer — widescreen, native XInput, draw distance and installer work**

Suggested post:

Hello Dethrace maintainers and contributors,

I've been working on a Windows-focused community project called **Carmageddon Dethrace Modernizer**, built on Dethrace v0.10.1:

Repository:
https://github.com/Bratwurstmensch/Carmageddon-Dethrace-Modernizer

Current v1.0-rc1 draft PR:
https://github.com/Bratwurstmensch/Carmageddon-Dethrace-Modernizer/pull/1

The current v1.0 release-candidate work combines several changes that may also be useful upstream:

- tested 854x480 16:9 presentation with centered original UI/video surfaces;
- full-width cockpit 3D rendering behind the original 4:3 cockpit artwork;
- rear-view mirror positioning for the widened framebuffer;
- native analog Xbox/XInput controls (left-stick steering, RT/LT analog accelerate/brake);
- 500-unit HiRes draw distance and related distant-detail work;
- separate 4:3 Modernizer runtime;
- OGG-first / WAV-fallback CD-audio support;
- Carmageddon + Splat Pack support.

The Modernizer itself also contains project-specific Windows installer work for user-owned game data, including GOG/eXoDOS-style sources, direct CUE/BIN SMK extraction and lossless Red Book audio extraction. No original Carmageddon or Splat Pack game data is intended to be redistributed. No public binary release has been published yet; this discussion is intentionally happening first.

The public source/build path has now been rebuilt through GitHub Actions and manually smoke-tested. The 4:3 runtime is stable in the tested scenarios. The 16:9 path is generally functional but still has a documented limitation: cockpit left/right look / rapid view switching can crash, especially near the beginning of a race. I do not want to hide that limitation.

Before publishing the first binary release, I wanted to ask two things:

1. **Licensing clarification:** the Dethrace repository currently contains a GPLv3 LICENSE, while older README wording still mentions public-domain/non-commercial terms. Which statement should downstream modified binary/source releases treat as authoritative?
2. **Upstream contributions:** would you be interested in any of the generally useful changes as separate, focused PRs rather than one large Modernizer PR?

The cleanest candidates seem to be:

- the small OGG-first/WAV-fallback CD-audio change;
- native analog XInput support (relevant to issue #343);
- draw-distance/LOD work (relevant to #457);
- widescreen work as a separate discussion/patch series (#349 / #518).

The goal is not to present the Modernizer as an official Dethrace build or to dump a large downstream patchset upstream. I'd rather keep contributions small and reviewable and follow the maintainers' preference.

Thanks for Dethrace and for making this project possible.
