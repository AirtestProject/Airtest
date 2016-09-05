#include "Minicap.hpp"

#include <errno.h>
#include <unistd.h>
#include <stdio.h>
#include <fcntl.h>
#include <math.h>

#include <binder/ProcessState.h>

#include <binder/IServiceManager.h>
#include <binder/IMemory.h>

#include <gui/ISurfaceComposer.h>
#include <gui/SurfaceComposerClient.h>

#include <private/gui/ComposerService.h>

#include <ui/DisplayInfo.h>
#include <ui/PixelFormat.h>

#include "mcdebug.h"

static const char*
error_name(int32_t err) {
  switch (err) {
  case android::NO_ERROR: // also android::OK
    return "NO_ERROR";
  case android::UNKNOWN_ERROR:
    return "UNKNOWN_ERROR";
  case android::NO_MEMORY:
    return "NO_MEMORY";
  case android::INVALID_OPERATION:
    return "INVALID_OPERATION";
  case android::BAD_VALUE:
    return "BAD_VALUE";
  case android::BAD_TYPE:
    return "BAD_TYPE";
  case android::NAME_NOT_FOUND:
    return "NAME_NOT_FOUND";
  case android::PERMISSION_DENIED:
    return "PERMISSION_DENIED";
  case android::NO_INIT:
    return "NO_INIT";
  case android::ALREADY_EXISTS:
    return "ALREADY_EXISTS";
  case android::DEAD_OBJECT: // also android::JPARKS_BROKE_IT
    return "DEAD_OBJECT";
  case android::FAILED_TRANSACTION:
    return "FAILED_TRANSACTION";
  case android::BAD_INDEX:
    return "BAD_INDEX";
  case android::NOT_ENOUGH_DATA:
    return "NOT_ENOUGH_DATA";
  case android::WOULD_BLOCK:
    return "WOULD_BLOCK";
  case android::TIMED_OUT:
    return "TIMED_OUT";
  case android::UNKNOWN_TRANSACTION:
    return "UNKNOWN_TRANSACTION";
  case android::FDS_NOT_ALLOWED:
    return "FDS_NOT_ALLOWED";
  default:
    return "UNMAPPED_ERROR";
  }
}

class MinicapImpl: public Minicap {
public:
  MinicapImpl(int32_t displayId)
    : mDisplayId(displayId),
      mComposer(android::ComposerService::getComposerService()),
      mDesiredWidth(0),
      mDesiredHeight(0) {
  }

  virtual
  ~MinicapImpl() {
    release();
  }

  virtual int
  applyConfigChanges() {
    mUserFrameAvailableListener->onFrameAvailable();
    return 0;
  }

  virtual int
  consumePendingFrame(Minicap::Frame* frame) {
    uint32_t width, height;
    android::PixelFormat format;
    android::status_t err;

    mHeap = NULL;
    err = mComposer->captureScreen(mDisplayId, &mHeap,
      &width, &height, &format, mDesiredWidth, mDesiredHeight, 0, -1UL);

    if (err != android::NO_ERROR) {
      MCERROR("ComposerService::captureScreen() failed %s", error_name(err));
      return err;
    }

    frame->data = mHeap->getBase();
    frame->width = width;
    frame->height = height;
    frame->format = convertFormat(format);
    frame->stride = width;
    frame->bpp = android::bytesPerPixel(format);
    frame->size = mHeap->getSize();

    return 0;
  }

  virtual Minicap::CaptureMethod
  getCaptureMethod() {
    return METHOD_SCREENSHOT;
  }

  virtual int32_t
  getDisplayId() {
    return mDisplayId;
  }

  virtual void
  release() {
    mHeap = NULL;
  }

  virtual void
  releaseConsumedFrame(Minicap::Frame* /* frame */) {
    mHeap = NULL;
    return mUserFrameAvailableListener->onFrameAvailable();
  }

  virtual int
  setDesiredInfo(const Minicap::DisplayInfo& info) {
    mDesiredWidth = info.width;
    mDesiredHeight = info.height;
    return 0;
  }

  virtual void
  setFrameAvailableListener(Minicap::FrameAvailableListener* listener) {
    mUserFrameAvailableListener = listener;
  }

  virtual int
  setRealInfo(const Minicap::DisplayInfo& info) {
    return 0;
  }

private:
  int32_t mDisplayId;
  android::sp<android::ISurfaceComposer> mComposer;
  android::sp<android::IMemoryHeap> mHeap;
  uint32_t mDesiredWidth;
  uint32_t mDesiredHeight;
  Minicap::FrameAvailableListener* mUserFrameAvailableListener;

  static Minicap::Format
  convertFormat(android::PixelFormat format) {
    switch (format) {
    case android::PIXEL_FORMAT_NONE:
      return FORMAT_NONE;
    case android::PIXEL_FORMAT_CUSTOM:
      return FORMAT_CUSTOM;
    case android::PIXEL_FORMAT_TRANSLUCENT:
      return FORMAT_TRANSLUCENT;
    case android::PIXEL_FORMAT_TRANSPARENT:
      return FORMAT_TRANSPARENT;
    case android::PIXEL_FORMAT_OPAQUE:
      return FORMAT_OPAQUE;
    case android::PIXEL_FORMAT_RGBA_8888:
      return FORMAT_RGBA_8888;
    case android::PIXEL_FORMAT_RGBX_8888:
      return FORMAT_RGBX_8888;
    case android::PIXEL_FORMAT_RGB_888:
      return FORMAT_RGB_888;
    case android::PIXEL_FORMAT_RGB_565:
      return FORMAT_RGB_565;
    case android::PIXEL_FORMAT_BGRA_8888:
      return FORMAT_BGRA_8888;
    case android::PIXEL_FORMAT_RGBA_5551:
      return FORMAT_RGBA_5551;
    case android::PIXEL_FORMAT_RGBA_4444:
      return FORMAT_RGBA_4444;
    default:
      return FORMAT_UNKNOWN;
    }
  }
};

int
minicap_try_get_display_info(int32_t displayId, Minicap::DisplayInfo* info) {
  android::DisplayInfo dinfo;
  android::status_t err = android::SurfaceComposerClient::getDisplayInfo(displayId, &dinfo);

  if (err != android::NO_ERROR) {
    MCERROR("SurfaceComposerClient::getDisplayInfo() failed: %s (%d)\n", error_name(err), err);
    return err;
  }

  info->width = dinfo.w;
  info->height = dinfo.h;
  info->orientation = dinfo.orientation;
  info->fps = dinfo.fps;
  info->density = dinfo.density;
  info->xdpi = dinfo.xdpi;
  info->ydpi = dinfo.ydpi;
  info->secure = false;
  info->size = sqrt(pow(dinfo.w / dinfo.xdpi, 2) + pow(dinfo.h / dinfo.ydpi, 2));

  return 0;
}

Minicap*
minicap_create(int32_t displayId) {
  return new MinicapImpl(displayId);
}

void
minicap_free(Minicap* mc) {
  delete mc;
}

void
minicap_start_thread_pool() {
  android::ProcessState::self()->startThreadPool();
}
