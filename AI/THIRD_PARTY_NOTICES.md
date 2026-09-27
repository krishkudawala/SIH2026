# Third-Party Notices & Licenses

Mandi Nyaay incorporates and utilizes open-source software libraries. This document records the software components, exact versions, licenses, and official attribution notices.

---

## 1. Currently Installed Dependencies (Development & Core)

### OpenCV (`opencv-python`)
* **Version**: `5.0.0.93` (or `4.9.0+`)
* **Upstream**: OpenCV Foundation (https://opencv.org/)
* **License**: Apache License 2.0
* **Notice**:
  ```
  Copyright 2000-2024, Intel Corporation, all rights reserved.
  Copyright 2009-2011, Willow Garage Inc., all rights reserved.
  Copyright 2009-2016, NVIDIA Corporation, all rights reserved.
  Copyright 2010-2013, Advanced Micro Devices, Inc., all rights reserved.
  Copyright 2015-2024, OpenCV Foundation, all rights reserved.
  Licensed under the Apache License, Version 2.0 (the "License").
  ```

### NumPy (`numpy`)
* **Version**: `2.5.3`
* **Upstream**: NumPy Developers (https://numpy.org/)
* **License**: BSD 3-Clause License
* **Notice**:
  ```
  Copyright (c) 2005-2024, NumPy Developers.
  All rights reserved.
  ```

### Pydantic (`pydantic` & `pydantic-core`)
* **Version**: `2.13.5` / `2.46.5`
* **Upstream**: Samuel Colvin & Pydantic Contributors (https://pydantic.dev/)
* **License**: MIT License
* **Notice**:
  ```
  The MIT License (MIT)
  Copyright (c) 2017 to present Pydantic Services Inc. and individual contributors.
  ```

### PyYAML (`pyyaml`)
* **Version**: `6.0.3`
* **Upstream**: Kirill Simonov & Ingy döt Net (https://pyyaml.org/)
* **License**: MIT License
* **Notice**:
  ```
  Copyright (c) 2017-2020 Ingy döt Net
  Copyright (c) 2006-2016 Kirill Simonov
  ```

### pytest (`pytest`)
* **Version**: `9.1.1`
* **Upstream**: Holger Krekel and pytest-dev team (https://pytest.org/)
* **License**: MIT License
* **Notice**:
  ```
  The MIT License (MIT)
  Copyright (c) 2004-2024 Holger Krekel and others
  ```

---

## 2. Planned / Evaluated Infrastructure Components

### Meta SAM 2 (Segment Anything 2)
* **Status**: Research / Internal Annotation Tooling Only
* **Upstream**: Meta Platforms, Inc. (https://github.com/facebookresearch/segment-anything-2)
* **License**: Apache License 2.0
* **Scope**: Permitted for dataset annotation acceleration. Excluded from deployable runtime bundle.

### Computer Vision Annotation Tool (CVAT)
* **Status**: Internal Data Platform
* **Upstream**: CVAT.ai Corporation (https://github.com/cvat-ai/cvat)
* **License**: MIT License
* **Scope**: Permitted for data annotation management. Standalone decoupled tool.

### ONNX Runtime
* **Status**: Mobile Edge Deployment Target
* **Upstream**: Microsoft Corporation (https://github.com/microsoft/onnxruntime)
* **License**: MIT License
* **Scope**: Permitted for commercial and institutional edge mobile inference.
