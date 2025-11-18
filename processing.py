''' 
Contains all processing code. 

Responsibilities:
  - Reading input and noise audio files
  - Performing noise cancellation / filtering
  - Returning processed audio to the GUI
  - Saving processed audio to disk
'''
from typing import Tuple


def read_audio(path: str) -> Tuple["numpy.ndarray", int]:
  """Read an audio file and return (y, sr).

  - `y` is a 1D or 2D numpy array (float32). If multi-channel, shape is (n_samples, n_channels).
  - `sr` is the sample rate (int).
  """
  try:
    import soundfile as sf
    import numpy as np
  except Exception:
    raise ImportError(
      "The `soundfile` and `numpy` packages are required to read audio.\n"
      "Install with: pip install soundfile numpy"
    )

  # soundfile path
  try:
    data, sr = sf.read(path, dtype="float32")
  except RuntimeError as e:
    # soundfile may fail on some compressed formats or MP3 (WIP)
    raise RuntimeError(
      f"soundfile failed to read '{path}': {e}"
    )

  return data, sr


def read_audio_mono(path: str) -> Tuple["numpy.ndarray", int]:
  """Read audio and return a mono float32 array and sample rate.

  If the file is stereo (or multi-channel) the channels are averaged.
  """
  import numpy as np

  y, sr = read_audio(path)
  if y.ndim == 1:
    return y, sr
  # average across channels -> shape (n_samples,)
  mono = np.mean(y, axis=1).astype("float32")
  return mono, sr


if __name__ == "__main__":
  # Small manual test: `python processing.py noisy.wav noise.wav`
  import sys

  if len(sys.argv) < 2:
    print("Usage: python processing.py <audio-file> [<other-audio-file>]")
    raise SystemExit(1)

  for p in sys.argv[1:]:
    try:
      y, sr = read_audio(p)
      import numpy as _np

      duration = float(len(y)) / sr if y.ndim == 1 else float(y.shape[0]) / sr
      print(f"Read '{p}': shape={_np.shape(y)}, sr={sr}, duration={duration:.2f}s")
    except Exception as exc:
      print(f"Failed to read '{p}': {exc}")
