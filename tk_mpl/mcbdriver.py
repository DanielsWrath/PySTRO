from ctypes import *
import numpy as np

class MCBDriver:
    error_codes = {
         0: 'No error (maybe an MCB warning)',
         1: 'Det handle or other parameter is invalid',
         2: 'MCB reported error (see nMacro_err & nMicro_err)',
         3: 'Disk, Network or MCB I/O error (see nMacro_err)',
        -1: 'Detector Comm Broken, Call MIOCloseDetector()',
        -2: 'Detector communication timeout -- Try Again',
        -3: 'Detector communication error -- Try Again',
        -4: 'Too Many open detectors -- close detector then try again',
        -5: 'Disk, OS or any other error',
         4: 'Memory allocation error',
         5: 'Authorization or Password failure ',
         8: 'MCBCIO call before MIOStartup() or after MIOCleanup()',
         9: 'Connection not open, Used only by UMCBI.OCX',
        10: 'Unexpected internal error, Used only by UMCBI.OCX',
        11: 'Requested operation is not supported by MCB <6.00>'
    }

    macro_codes = {
          0: 'Success',
          1: 'Power-up just occurred',
          2: 'Battery-backed data lost',
        129: 'Command syntax error',
        131: 'Command execution error',
        132: 'Invalid Command'
    }

    macro_error_codes = {
          1: 'Invalid Verb',
          2: 'Invalid Noun',
          4: 'Invalid Modifier',
        128: 'Invalid first parameter',
        129: 'Invalid second parameter',
        130: 'Invalid third parameter',
        131: 'Invalid fourth parameter',
        132: 'Invalid number of parameters',
        133: 'Invalid command',
        134: 'Response buffer too small',
        135: 'Not applicable while active',
        136: 'Invalid command in this mode',
        137: 'Hardware error',
        138: 'Requested data not found'
    }

    micro_codes = {
          0: 'Success',
          1: 'Input already started/stopped',
          2: 'Preset already exceeded',
          4: 'Input not stared/stopped',
         64: 'Parameter was rounded (for decimal numbers)',
        128: 'No sample data available'
    }

    def __init__(self):
        self.driver = windll.LoadLibrary(r'C:\windows\system32\mcbcio32.dll')
        assert self.driver.MIOStartup() == 1, 'Startup Failed'
        
    def __del__(self):
        assert self.driver.MIOCleanup() == 1, 'Cleanup Failed'

    def get_last_error(self):
        macro_err = c_int()
        micro_err = c_int()
        error = self.driver.MIOGetLastError(byref(macro_err), byref(micro_err))
        
        err_msg = error_codes[error]
        mac_msg = macro_codes[macro_err.value]
        if macro_err.value == 129 or macro_err.value == 131:
            mic_msg = macro_error_codes[micr_erro.value]
        else:
            mic_msg = micro_codes[micro_err.value]
        return err_msg, mac_msg, mic_msg
        
    def open_detector(self, ndet):
        hdet = self.driver.MIOOpenDetector(ndet, '', '')
        assert hdet > 0, 'Open Detector Failed'
        return hdet
        
    def close_detector(self, hdet):
        assert self.driver.MIOCloseDetector(hdet) == 1, 'Close Detector Failed'
        
    def comm(self, hdet, cmd):
        max_resp = 128
        resp = create_string_buffer(max_resp)
        assert self.driver.MIOComm(hdet, cmd.encode(), '', '', max_resp,\
            resp, 0) == 1, 'Command Failed'
        return resp.value
        
    def get_config_max(self):
        det_max = c_int32()
        assert self.driver.MIOGetConfigMax('', byref(det_max)) == 1,\
            'Get Config Max Failed'
        return det_max.value
        
    def get_config_name(self, ndet):
        name_max = 128
        name = create_string_buffer(name_max)
        id = c_int()
        assert self.driver.MIOGetConfigName(ndet, '', name_max, name,\
            byref(id), 0) == 1, 'Get Config Name Failed'
        return name.value, id.value
        
    def get_data(self, hdet, start_chan=0, num_chans=2048):
        assert start_chan + num_chans <= 2048, 'Invalid Parameters in Get Data'
        buffer = np.zeros(num_chans, dtype=np.int32)
        assert self.driver.MIOGetData(hdet, start_chan, num_chans,\
            buffer.ctypes.data_as(POINTER(c_int32)), 0, 0, 0, '') > 0,\
            'Get Data Failed'
        return buffer
        
    def set_data(self, hdet, buffer, start_chan=0, num_chans=2048):
        assert self.driver.MIOSetData(hdet, start_chan, num_chans,\
            buffer.ctypes.data_as(POINTER(c_int32)), '') > 0, 'Set Data Failed'
            
    def is_active(self, hdet):
        return self.driver.MIOIsActive(hdet) == 1