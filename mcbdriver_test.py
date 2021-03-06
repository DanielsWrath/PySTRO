from ctypes import *
import numpy as np
from time import time

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
        self.active = False
        self.buffer = np.zeros(2048)
        self.roi_mask = np.full(2048, False)
        self.true = 0
        self.live = 0
        self.true_preset = 0
        self.live_preset = 0
        self.gate = 'OFF'
        self.lld = 0
        self.uld = 2047
        self.start_time = int(time())
        self.window = (0, 2048)

    def __del__(self):
        pass

    def get_det_length(self, hdet):
        return 2048

    def get_last_error(self):
        return '', '', ''

    def open_detector(self, ndet):
        return 0

    def close_detector(self, hdet):
        pass

    def comm(self, hdet, cmd):
        resp = ''
        if cmd == 'START':
            self.active = True
            self.buffer = np.arange(2048)
            self.start_time = int(time())
        if cmd == 'STOP':
            self.active = False
        if cmd == 'CLEAR':
            self.buffer = np.zeros(2048)
            self.true = 0
            self.live = 0
        if cmd == 'CLEAR_ROI':
            start_chan, num_chans = self.window
            for i in range(num_chans):
                self.roi_mask[start_chan + i] = False
        if cmd == 'SHOW_TRUE':
            resp = '$G{0:010d}cccn'.format(self.true)
        if cmd == 'SHOW_LIVE':
            resp = '$G{0:010d}cccn'.format(self.live)
        if cmd == 'SHOW_TRUE_PRESET':
            resp = '$G{0:010d}cccn'.format(self.true_preset)
        if cmd == 'SHOW_LIVE_PRESET':
            resp = '$G{0:010d}cccn'.format(self.live_preset)
        if cmd == 'SHOW_GATE':
            resp = '$F0' + self.gate + 'n'
        if cmd == 'SHOW_LLD':
            resp = '$C{0:05d}cccn'.format(self.lld)
        if cmd == 'SHOW_ULD':
            resp = '$C{0:05d}cccn'.format(self.uld)
        if cmd == 'SHOW_ROI':
            self.reached_end = False
            self.roi_search = 0
            while not self.roi_mask[self.roi_search]:
                if self.roi_search == 2047:
                    self.reached_end = True
                    break
                self.roi_search += 1
            if not self.reached_end:
                start_chan = self.roi_search
                while self.roi_mask[self.roi_search]:
                    if self.roi_search == 2047:
                        self.reached_end = True
                        break
                    self.roi_search += 1
                if not self.reached_end:
                    num_chans = self.roi_search-start_chan
                else:
                    num_chans = 2048-start_chan
            else:
                start_chan = 0
                num_chans = 0
            resp = '$D{0:05d}{1:05d}cccn'.format(start_chan, num_chans)
        if cmd == 'SHOW_NEXT':
            while not self.roi_mask[self.roi_search]:
                if self.roi_search == 2047:
                    self.reached_end = True
                    break
                self.roi_search += 1
            if not self.reached_end:
                start_chan = self.roi_search
                while self.roi_mask[self.roi_search]:
                    if self.roi_search == 2047:
                        self.reached_end = True
                        break
                    self.roi_search += 1
                if not self.reached_end:
                    num_chans = self.roi_search-start_chan
                else:
                    num_chans = 2048-start_chan
            else:
                start_chan = 0
                num_chans = 0
            resp = '$D{0:05d}{1:05d}cccn'.format(start_chan, num_chans)
        if cmd[:9] == 'SET_TRUE ':
            self.true = int(cmd[9:])
        if cmd[:9] == 'SET_LIVE ':
            self.live = int(cmd[9:])
        if cmd[:9] == 'SET_TRUE_':
            self.true_preset = int(cmd[16:])
        if cmd[:9] == 'SET_LIVE_':
            self.live_preset = int(cmd[16:])
        if cmd[:8] == 'SET_GATE':
            self.gate = cmd[9:]
        if cmd[:7] == 'SET_LLD':
            self.lld = int(cmd[8:])
        if cmd[:7] == 'SET_ULD':
            self.uld = int(cmd[8:])
        if cmd[:8] == 'SET_DATA':
            start_chan, num_chans, value = map(int, cmd[9:].split(','))
            for i in range(num_chans):
                self.buffer[start_chan + i] = value
        if cmd[:7] == 'SET_ROI':
            start_chan, num_chans = map(int, cmd[8:].split(','))
            for i in range(num_chans):
                self.roi_mask[start_chan + i] = True
        if cmd[:10] == 'SET_WINDOW':
            if len(cmd) < 12:
                self.window = (0, 2048)
            else:
                start_chan, num_chans = map(int, cmd[11:].split(','))
                self.window = (start_chan, num_chans)
        return resp

    def get_config_max(self):
        return 1

    def get_config_name(self, ndet):
        return 'test', 1

    def get_data(self, hdet, start_chan=0, num_chans=2048):
        return self.buffer, self.roi_mask

    def get_start_time(self, hdet):
        return self.start_time

    def is_active(self, hdet):
        return self.active