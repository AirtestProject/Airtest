LOCAL_PATH := $(abspath $(call my-dir))
include $(CLEAR_VARS)

LOCAL_MODULE := minicap-shared

LOCAL_MODULE_FILENAME := minicap

LOCAL_SRC_FILES := \
	mock/Minicap.cpp \

LOCAL_C_INCLUDES := \
	$(LOCAL_PATH)/aosp/include \

LOCAL_EXPORT_C_INCLUDES := \
	$(LOCAL_PATH)/aosp/include \

include $(BUILD_SHARED_LIBRARY)
