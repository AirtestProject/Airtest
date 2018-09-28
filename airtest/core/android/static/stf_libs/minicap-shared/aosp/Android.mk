LOCAL_PATH := $(call my-dir)
include $(CLEAR_VARS)

LOCAL_MODULE := minicap

LOCAL_MODULE_TAGS := optional

ifneq ($(OVERRIDE_PLATFORM_SDK_VERSION),)
LOCAL_SRC_FILES += src/minicap_$(OVERRIDE_PLATFORM_SDK_VERSION).cpp
else ifeq ($(PLATFORM_SDK_VERSION),28)
LOCAL_SRC_FILES += src/minicap_28.cpp
else ifeq ($(PLATFORM_SDK_VERSION),27)
LOCAL_SRC_FILES += src/minicap_27.cpp
else ifeq ($(PLATFORM_SDK_VERSION),26)
LOCAL_SRC_FILES += src/minicap_26.cpp
else ifeq ($(PLATFORM_SDK_VERSION),25)
LOCAL_SRC_FILES += src/minicap_25.cpp
else ifeq ($(PLATFORM_SDK_VERSION),24)
LOCAL_SRC_FILES += src/minicap_24.cpp
else ifeq ($(PLATFORM_SDK_VERSION),23)
LOCAL_SRC_FILES += src/minicap_23.cpp
else ifeq ($(PLATFORM_SDK_VERSION),22)
LOCAL_SRC_FILES += src/minicap_22.cpp
else ifeq ($(PLATFORM_SDK_VERSION),21)
LOCAL_SRC_FILES += src/minicap_21.cpp
else ifeq ($(PLATFORM_SDK_VERSION),19)
LOCAL_SRC_FILES += src/minicap_19.cpp
else ifeq ($(PLATFORM_SDK_VERSION),18)
LOCAL_SRC_FILES += src/minicap_18.cpp
else ifeq ($(PLATFORM_SDK_VERSION),17)
LOCAL_SRC_FILES += src/minicap_17.cpp
else ifeq ($(PLATFORM_SDK_VERSION),16)
LOCAL_SRC_FILES += src/minicap_16.cpp
else ifeq ($(PLATFORM_SDK_VERSION),15)
LOCAL_SRC_FILES += src/minicap_14.cpp
else ifeq ($(PLATFORM_SDK_VERSION),14)
LOCAL_SRC_FILES += src/minicap_14.cpp
else ifeq ($(PLATFORM_SDK_VERSION),10)
LOCAL_SRC_FILES += src/minicap_9.cpp
else ifeq ($(PLATFORM_SDK_VERSION),9)
LOCAL_SRC_FILES += src/minicap_9.cpp
endif

LOCAL_PRELINK_MODULE := false

LOCAL_SHARED_LIBRARIES := \
	libcutils \
	libutils \
	libbinder \
	libui \
	liblog \

ifeq ($(PLATFORM_SDK_VERSION),$(filter $(PLATFORM_SDK_VERSION),10 9))
LOCAL_SHARED_LIBRARIES += libsurfaceflinger_client
else
LOCAL_SHARED_LIBRARIES += libgui
endif

LOCAL_C_INCLUDES += \
	$(LOCAL_PATH)/include \

LOCAL_CFLAGS += -DPLATFORM_SDK_VERSION=$(PLATFORM_SDK_VERSION)

include $(BUILD_SHARED_LIBRARY)
