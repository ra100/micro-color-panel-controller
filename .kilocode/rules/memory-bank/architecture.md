# System Architecture

## Source Code Paths

### Core Components

- `src/core/device.py` - Main USB device interface and communication layer
- `src/core/input_parser.py` - HID input report parsing and event generation
- `blender_addon/device_control.py` - Standalone device control module for Blender addon

### Application Integrations

- `src/applications/blender.py` - Blender addon implementation
- `blender_addon/__init__.py` - Self-contained Blender addon with UI

### Configuration & Data

- `davinci_panel_mapping.json` - Machine-readable control mapping
- `davinci_panel_controls.py` - Python constants for development
- `udev/99-davinci-micro-panel.rules` - Linux USB permissions

### Investigation & Development Tools

- `investigation/` - 25+ tools for reverse engineering and testing
- `data/` - Generated data and raw USB captures

## Key Technical Decisions

### USB Communication Architecture

- **Interface 2 (HID)**: Primary interface for input/output communication
- **Report-based Protocol**: Uses HID reports (0x02, 0x05, 0x06) for different data types
- **Dual Command Pattern**: Secondary control (0x0a) required for stable illumination
- **Automatic Recovery**: Built-in reconnection logic for USB stability

### Control Mapping Strategy

- **Hardware Discovery**: Systematic reverse engineering identified 61+ functional controls
- **Trackball Limitations**: Only LEFT and CENTER trackballs connected to USB
- **Button Bit-mapping**: 52 buttons packed into 8-byte reports with bit patterns
- **Encoder Multi-byte**: Complex encoder data spanning multiple bytes

### Application Integration Pattern

- **Plugin Architecture**: Modular design for adding new applications
- **Callback System**: Event-driven input processing with configurable callbacks
- **Sensitivity Control**: User-adjustable sensitivity and axis inversion
- **Timer-based Polling**: Blender-compatible input monitoring using timers

## Design Patterns

### Device Abstraction

- **Context Manager**: Device class supports `with` statement for automatic cleanup
- **State Management**: Connection state tracking with automatic recovery
- **Error Handling**: Graceful degradation and reconnection on USB errors

### Input Processing Pipeline

- **Raw Data → Events**: Multi-stage parsing from HID reports to structured events
- **Filtering & Smoothing**: Weighted averaging for trackball movement stability
- **Callback Dispatch**: Type-based event routing to application handlers

### Cross-Platform Compatibility

- **USB Library Abstraction**: PyUSB for cross-platform USB access
- **Path Independence**: Relative imports and configurable paths
- **Dependency Management**: Conda environment with pip fallbacks

## Component Relationships

### Device Layer (Bottom)

```
USB Hardware → device.py → Input Events
```

### Processing Layer (Middle)

```
Input Events → input_parser.py → Structured Events → Callbacks
```

### Application Layer (Top)

```
Structured Events → blender.py → Blender Actions
```

### Data Flow

1. **USB Input** → HID reports read from endpoint 0x81
2. **Parsing** → Reports decoded into button/encoder/trackball events
3. **Processing** → Events filtered, smoothed, and scaled
4. **Application** → Events mapped to specific application functions
5. **Feedback** → Illumination and display updates sent to panel

## Critical Implementation Paths

### Connection Establishment

1. USB device discovery (VID: 1edb, PID: da0f)
2. Kernel driver detachment from interface 2
3. Interface claiming and endpoint access
4. Secondary control initialization (report 0x0a)
5. Illumination activation (report 0x03)

### Input Processing Loop

1. Read HID input reports with timeout
2. Parse report ID and extract data fields
3. Apply filtering and sensitivity scaling
4. Dispatch events to registered callbacks
5. Handle USB errors with reconnection logic

### Illumination Maintenance

1. Periodic brightness refresh every 15 seconds
2. Secondary control command before illumination
3. Non-linear brightness mapping (0-255 range)
4. Automatic recovery on illumination failure
