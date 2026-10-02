Carmageddon Dethrace Modernizer - package source
================================================

This directory contains the launcher/controller source intended for the future
runtime package.

It intentionally does NOT contain:
- dethrace-16x9-v1.5.exe
- original Carmageddon DATA
- original Splat Pack CARSPLAT data

The current scripts expect the final runtime layout to contain:

  dethrace-16x9-v1.5.exe
  DATA\...
  CARSPLAT\...                  (optional, for Splat Pack)
  Controller\Carmageddon-XInput.ps1
  Controller\Carmageddon-SplatPack-XInput.ps1

Until the validated v1.5 binary changes have been reproduced from public source,
this directory should be treated as development/package source rather than a
complete downloadable game package.
