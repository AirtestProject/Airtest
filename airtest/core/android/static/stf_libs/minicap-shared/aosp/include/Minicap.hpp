#ifndef MINICAP_HPP
#define MINICAP_HPP

#include <cstdint>

class Minicap {
public:
  enum CaptureMethod {
    METHOD_FRAMEBUFFER      = 1,
    METHOD_SCREENSHOT       = 2,
    METHOD_VIRTUAL_DISPLAY  = 3,
  };

  enum Format {
    FORMAT_NONE          = 0x01,
    FORMAT_CUSTOM        = 0x02,
    FORMAT_TRANSLUCENT   = 0x03,
    FORMAT_TRANSPARENT   = 0x04,
    FORMAT_OPAQUE        = 0x05,
    FORMAT_RGBA_8888     = 0x06,
    FORMAT_RGBX_8888     = 0x07,
    FORMAT_RGB_888       = 0x08,
    FORMAT_RGB_565       = 0x09,
    FORMAT_BGRA_8888     = 0x0a,
    FORMAT_RGBA_5551     = 0x0b,
    FORMAT_RGBA_4444     = 0x0c,
    FORMAT_UNKNOWN       = 0x00,
  };

  enum Orientation {
    ORIENTATION_0    = 0,
    ORIENTATION_90   = 1,
    ORIENTATION_180  = 2,
    ORIENTATION_270  = 3,
  };

  struct DisplayInfo {
    uint32_t width;
    uint32_t height;
    float fps;
    float density;
    float xdpi;
    float ydpi;
    float size;
    uint8_t orientation;
    bool secure;
  };

  struct Frame {
    void const* data;
    Format format;
    uint32_t width;
    uint32_t height;
    uint32_t stride;
    uint32_t bpp;
    size_t size;
  };

  struct FrameAvailableListener {
    virtual
    ~FrameAvailableListener() {}

    virtual void
    onFrameAvailable() = 0;
  };

  Minicap() {}

  virtual
  ~Minicap() {}

  // Applies changes made by setDesiredInfo() and setRealInfo(). Must be
  // called before attempting to wait or consume frames.
  virtual int
  applyConfigChanges() = 0;

  // Consumes a frame. Must be called after waitForFrame().
  virtual int
  consumePendingFrame(Frame* frame) = 0;

  // Peek behind the scenes to see which capture method is actually
  // being used.
  virtual CaptureMethod
  getCaptureMethod() = 0;

  // Get display ID.
  virtual int32_t
  getDisplayId() = 0;

  // Release all resources.
  virtual void
  release() = 0;

  // Releases a consumed frame so that it can be reused by Android again.
  // Must be called before consumePendingFrame() is called again.
  virtual void
  releaseConsumedFrame(Frame* frame) = 0;

  // Set desired information about the display. Currently, only the
  // following properties are actually used: width, height and orientation.
  // After the configuration has been applied, new frames should satisfy
  // the requirements.
  virtual int
  setDesiredInfo(const DisplayInfo& info) = 0;

  // Sets the frame available listener.
  virtual void
  setFrameAvailableListener(FrameAvailableListener* listener) = 0;

  // Set the display's real information. This cannot be accessed automatically
  // due to manufacturers (mainly Samsung) having customized
  // android::DisplayInfo. The information has to be gathered somehow and then
  // passed on here. Currently only the following properties are actually
  // used: width and height.
  virtual int
  setRealInfo(const DisplayInfo& info) = 0;
};

// Attempt to get information about the given display. This may segfault
// on some devices due to manufacturer (mainly Samsung) customizations.
int
minicap_try_get_display_info(int32_t displayId, Minicap::DisplayInfo* info);

// Creates a new Minicap instance for the current platform.
Minicap*
minicap_create(int32_t displayId);

// Frees a Minicap instance. Don't call delete yourself as it won't have
// access to the platform-specific modifications.
void
minicap_free(Minicap* mc);

// Starts an Android thread pool. Must be called before doing anything else.
void
minicap_start_thread_pool();

#endif
