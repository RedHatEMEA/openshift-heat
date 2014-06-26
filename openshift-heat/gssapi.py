#!/usr/bin/python
#
# Copyright 2014 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import ctypes

try:
    gssapi = ctypes.cdll.LoadLibrary("/usr/lib64/libgssapi_krb5.so.2")
except:
    pass

# constants

GSS_C_BOTH = 0
GSS_C_INITIATE = 1
GSS_C_ACCEPT = 2

GSS_C_GSS_CODE = 1
GSS_C_MECH_CODE = 2

GSS_C_NT_HOSTBASED_SERVICE = "GSS_C_NT_HOSTBASED_SERVICE"
GSS_C_NT_USER_NAME = "GSS_C_NT_USER_NAME"

_NULL = ctypes.c_void_p(0)

# types


class gss_buffer_t(ctypes.Structure):
    # Notice: any given gss_buffer_t instance must be used either as an input
    # value to a GSSAPI call, or to receive a return value from it, but not
    # both.
    #
    # If a gss_buffer_t instance is initialised with a value, it must be used
    # only as an input value to GSSAPI; python retains normal control of the
    # memory management of the underlying buffer.
    #
    # If a gss_buffer_t instance is not initialised with a value, it must be
    # used only to receive a return value from GSSAPI.  GSSAPI will allocate
    # the memory used by the buffer; upon deletion of the gss_buffer_t
    # instance, gss_release_buffer() will be called so that GSSAPI can
    # deallocate the memory it allocated.

    _fields_ = [("length", ctypes.c_size_t),
                ("value", ctypes.c_void_p)]

    def __init__(self, s=None):
        super(gss_buffer_t, self).__init__()

        self.output = s is None

        if s:
            self.s = s  # keep a reference to s, because cast doesn't
            if isinstance(self.s, unicode):
                self.s = s.encode("utf-8")
            self.length = len(self.s)
            self.value = ctypes.cast(self.s, ctypes.c_void_p)

    def __del__(self):
        if self.output:
            _gss_release_buffer(self)

    def __str__(self):
        return ctypes.string_at(self.value, self.length)


class gss_key_value_element_struct(ctypes.Structure):
    _fields_ = [("key", ctypes.c_char_p),
                ("value", ctypes.c_char_p)]


class gss_key_value_set_struct(ctypes.Structure):
    _fields_ = [("count", ctypes.c_uint32),
                ("elements", ctypes.POINTER(gss_key_value_element_struct))]

# wrappers for GSSAPI opaque types, adding automatic deletion, follow.


class gss_name_t(ctypes.c_void_p):
    def __del__(self):
        if self:
            _gss_release_name(self)


class gss_cred_id_t(ctypes.c_void_p):
    def __del__(self):
        if self:
            _gss_release_cred(self)


class gss_ctx_id_t(ctypes.c_void_p):
    def __del__(self):
        if self:
            _gss_delete_sec_context(self)

# GSSAPIException is thrown whenever an error is returned from GSSAPI.


class GSSAPIException(Exception):
    def __init__(self, status, minor_status):
        super(GSSAPIException, self).__init__()
        (self.status, self.minor_status) = (status, minor_status)
        self.value = "\n%s\n%s" % (gss_display_status(status, GSS_C_GSS_CODE),
                                   gss_display_status(minor_status,
                                                      GSS_C_MECH_CODE))

    def __str__(self):
        return self.value

# functions


def gss_display_status(status, type):
    minor_status = ctypes.c_uint32()
    message_context = ctypes.c_uint32()  # TODO use message_context as designed
    status_string = gss_buffer_t()

    gssapi.gss_display_status(ctypes.byref(minor_status),
                              status,
                              ctypes.c_int(type),
                              _NULL,
                              ctypes.byref(message_context),
                              ctypes.byref(status_string))

    return str(status_string)


def _gss_release_buffer(buf):
    # Library end-users should not need to call this function.
    minor_status = ctypes.c_uint32()

    status = gssapi.gss_release_buffer(ctypes.byref(minor_status),
                                       ctypes.byref(buf))

    if status or minor_status:
        raise GSSAPIException(status, minor_status)


def gss_import_name(name, type):
    minor_status = ctypes.c_uint32()
    input_name_buffer = gss_buffer_t(name)
    output_name = gss_name_t()

    status = gssapi.gss_import_name(ctypes.byref(minor_status),
                                    ctypes.byref(input_name_buffer),
                                    ctypes.c_void_p.in_dll(gssapi, type),
                                    ctypes.byref(output_name))

    if status or minor_status:
        raise GSSAPIException(status, minor_status)

    return output_name


def _gss_release_name(name):
    # Library end-users should not need to call this function.
    minor_status = ctypes.c_uint32()

    status = gssapi.gss_release_name(ctypes.byref(minor_status), name)

    if status or minor_status:
        raise GSSAPIException(status, minor_status)


def gss_acquire_cred(name):
    minor_status = ctypes.c_uint32()
    output_cred_handle = gss_cred_id_t()

    status = gssapi.gss_acquire_cred(ctypes.byref(minor_status),
                                     name,
                                     ctypes.c_uint32(0),
                                     _NULL,
                                     ctypes.c_int(GSS_C_INITIATE),
                                     ctypes.byref(output_cred_handle),
                                     _NULL,
                                     _NULL)

    if status or minor_status:
        raise GSSAPIException(status, minor_status)

    return output_cred_handle


def gss_acquire_cred_from(store, name):
    minor_status = ctypes.c_uint32()
    cred_store = gss_key_value_set_struct(len(store),
                                          (gss_key_value_element_struct *
                                           len(store))(*store))

    output_cred_handle = gss_cred_id_t()

    status = gssapi.gss_acquire_cred_from(ctypes.byref(minor_status),
                                          name,
                                          ctypes.c_uint32(0),
                                          _NULL,
                                          ctypes.c_int(GSS_C_INITIATE),
                                          ctypes.byref(cred_store),
                                          ctypes.byref(output_cred_handle),
                                          _NULL,
                                          _NULL)

    if status or minor_status:
        raise GSSAPIException(status, minor_status)

    return output_cred_handle


def gss_acquire_cred_impersonate_name(cred, name):
    minor_status = ctypes.c_uint32()
    output_cred_handle = gss_cred_id_t()

    status = gssapi.gss_acquire_cred_impersonate_name(
        ctypes.byref(minor_status),
        cred,
        name,
        ctypes.c_uint32(0),
        _NULL,
        ctypes.c_int(GSS_C_INITIATE),
        ctypes.byref(output_cred_handle),
        _NULL,
        _NULL)

    if status or minor_status:
        raise GSSAPIException(status, minor_status)

    return output_cred_handle


def _gss_release_cred(cred):
    # Library end-users should not need to call this function.
    minor_status = ctypes.c_uint32()

    status = gssapi.gss_release_cred(ctypes.byref(minor_status), cred)

    if status or minor_status:
        raise GSSAPIException(status, minor_status)


def gss_init_sec_context(cred, name):
    minor_status = ctypes.c_uint32()
    context_handle = gss_ctx_id_t()
    token = gss_buffer_t()

    status = gssapi.gss_init_sec_context(ctypes.byref(minor_status),
                                         cred,
                                         ctypes.byref(context_handle),
                                         name,
                                         _NULL,
                                         ctypes.c_uint32(0),
                                         ctypes.c_uint32(0),
                                         _NULL,
                                         _NULL,
                                         _NULL,
                                         ctypes.byref(token),
                                         _NULL,
                                         _NULL)

    if status or minor_status:
        raise GSSAPIException(status, minor_status)

    return (context_handle, str(token))


def _gss_delete_sec_context(context):
    # Library end-users should not need to call this function.
    minor_status = ctypes.c_uint32()

    status = gssapi.gss_delete_sec_context(ctypes.byref(minor_status),
                                           context,
                                           _NULL)

    if status or minor_status:
        raise GSSAPIException(status, minor_status)
