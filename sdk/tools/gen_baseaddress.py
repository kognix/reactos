'''
PROJECT:     ReactOS baseaddress updater
LICENSE:     MIT (https://spdx.org/licenses/MIT)
PURPOSE:     Update baseaddresses of all modules
COPYRIGHT:   Copyright 2017,2018 Mark Jansen (mark.jansen@reactos.org)
'''
from __future__ import print_function, absolute_import, division
import os
import struct
import sys

try:
    import pefile
except ImportError:
    print('# Please install pefile from pip or https://github.com/erocarrera/pefile')
    print('# Using fallback')
    print()

ALL_EXTENSIONS = (
    '.dll', '.acm', '.ax', '.cpl', '.drv', '.ocx'
)

PRIORITIES = (
    'ntdll.dll',
    'kernel32.dll',
    'msvcrt.dll',
    'advapi32.dll',
    'gdi32.dll',
    'user32.dll',
    'dhcpcsvc.dll',
    'dnsapi.dll',
    'icmp.dll',
    'iphlpapi.dll',
    'ws2_32.dll',
    'ws2help.dll',
    'shlwapi.dll',
    'rpcrt4.dll',
    'comctl32.dll',
    'ole32.dll',
    'winspool.drv',
    'winmm.dll',
    'comdlg32.dll',
    'shell32.dll',
    'lz32.dll',
    'version.dll',
    'oleaut32.dll',
    'setupapi.dll',
    'mpr.dll',
    'crypt32.dll',
    'wininet.dll',
    'urlmon.dll',
    'psapi.dll',
    'imm32.dll',
    'msvfw32.dll',
    'dbghelp.dll',
    'devmgr.dll',
    'msacm32.dll',
    'netapi32.dll',
    'powrprof.dll',
    'secur32.dll',
    'wintrust.dll',
    'avicap32.dll',
    'cabinet.dll',
    'dsound.dll',
    'glu32.dll',
    'opengl32.dll',
    'riched20.dll',
    'smdll.dll',
    'userenv.dll',
    'uxtheme.dll',
    'cryptui.dll',
    'csrsrv.dll',
    'basesrv.dll',
    'winsrv.dll',
    'dplayx.dll',
    'gdiplus.dll',
    'msimg32.dll',
    'mswsock.dll',
    'oledlg.dll',
    'rasapi32.dll',
    'rsaenh.dll',
    'samlib.dll',
    'sensapi.dll',
    'sfc_os.dll',
    'snmpapi.dll',
    'spoolss.dll',
    'usp10.dll',
)

EXCLUDE = (
    'bmfd.dll',
    'bootvid.dll',
    'freeldr_pe.dll',
    'ftfd.dll',
    'fusion.dll',
    'hal.dll',
    'halaacpi.dll',
    'halacpi.dll',
    'halapic.dll',
    'kbda1.dll',
    'kbda2.dll',
    'kbda3.dll',
    'kbdal.dll',
    'kbdarme.dll',
    'kbdarmw.dll',
    'kbdaze.dll',
    'kbdazel.dll',
    'kbdbe.dll',
    'kbdbga.dll',
    'kbdbgm.dll',
    'kbdbgt.dll',
    'kbdblr.dll',
    'kbdbr.dll',
    'kbdbur.dll',
    'kbdcan.dll',
    'kbdcr.dll',
    'kbdcz.dll',
    'kbdcz1.dll',
    'kbdda.dll',
    'kbddv.dll',
    'kbdes.dll',
    'kbdest.dll',
    'kbdfc.dll',
    'kbdfi.dll',
    'kbdfr.dll',
    'kbdgeo.dll',
    'kbdgerg.dll',
    'kbdgneo.dll',
    'kbdgr.dll',
    'kbdgrist.dll',
    'kbdhe.dll',
    'kbdheb.dll',
    'kbdhu.dll',
    'kbdic.dll',
    'kbdinasa.dll',
    'kbdinben.dll',
    'kbdindev.dll',
    'kbdinguj.dll',
    'kbdinmal.dll',
    'kbdir.dll',
    'kbdit.dll',
    'kbdja.dll',
    'kbdkaz.dll',
    'kbdko.dll',
    'kbdla.dll',
    'kbdlt1.dll',
    'kbdlv.dll',
    'kbdmac.dll',
    'kbdne.dll',
    'kbdno.dll',
    'kbdpl.dll',
    'kbdpl1.dll',
    'kbdpo.dll',
    'kbdro.dll',
    'kbdru.dll',
    'kbdru1.dll',
    'kbdsg.dll',
    'kbdsk.dll',
    'kbdsk1.dll',
    'kbdsw.dll',
    'kbdtat.dll',
    'kbdth0.dll',
    'kbdth1.dll',
    'kbdth2.dll',
    'kbdth3.dll',
    'kbdtuf.dll',
    'kbdtuq.dll',
    'kbduk.dll',
    'kbdur.dll',
    'kbdurs.dll',
    'kbdus.dll',
    'kbdusa.dll',
    'kbdusl.dll',
    'kbdusr.dll',
    'kbdusx.dll',
    'kbduzb.dll',
    'kbdvntc.dll',
    'kbdycc.dll',
    'kbdycl.dll',
    'kdcom.dll',
    'kdvbox.dll',
    'setupldr_pe.dll',
    'vgaddi.dll',
    'dllexport_test_dll1.dll',
    'dllexport_test_dll2.dll',
    'dllimport_test.dll',
    'MyEventProvider.dll',
    'w32kdll_2k3sp2.dll',
    'w32kdll_ros.dll',
    'w32kdll_xpsp2.dll',
)


def size_of_image_fallback(filename):
    with open(filename, 'rb') as fin:
        if fin.read(2) != 'MZ':
            print(filename, 'No dos header found!')
            return 0
        fin.seek(0x3C)
        e_lfanew = struct.unpack('i', fin.read(4))[0]
        fin.seek(e_lfanew)
        if fin.read(4) != 'PE\0\0':
            print(filename, 'No PE header found!')
            return 0
        fin.seek(e_lfanew + 0x18)
        pe_magic = struct.unpack('h', fin.read(2))[0]
        if pe_magic != 0x10b:
            print(filename, 'is not a 32 bit exe!')
            return 0
        fin.seek(e_lfanew + 0x50)
        pe_size_of_image = struct.unpack('i', fin.read(4))[0]
        return pe_size_of_image

def size_of_image(filename):
    if 'pefile' in globals():
        return pefile.PE(filename, fast_load=True).OPTIONAL_HEADER.SizeOfImage
    return size_of_image_fallback(filename)


class Module(object):
    def __init__(self, name, address, size):
        self._name = name
        self.address = address
        self.size = size
        self._reserved = address != 0

    def gen_baseaddress(self):
        name, ext = os.path.splitext(self._name)
        postfix = ''
        if ext in('.acm', '.drv') and self._name != 'winspool.drv':
            name = self._name
        if name == 'ntdll':
            postfix = ' # should be above 0x%08x' % self.address
        elif self._reserved:
            postfix = ' # reserved'
        print('set(baseaddress_%-30s 0x%08x)%s' % (name, self.address, postfix))

    def end(self):
        return self.address + self.size

    def __repr__(self):
        return '%s (0x%08x - 0x%08x)' % (self._name, self.address, self.end())

class MemoryLayout(object):
    def __init__(self, startaddress):
        self.addresses = []
        self.found = {}
        self.reserved = {}
        self.initial = startaddress
        self.start_at = 0
        self.module_padding = 0x2000

    def add_reserved(self, name, address):
        self.reserved[name] = (address, 0)

    def add(self, filename, name):
        size = size_of_image(filename)
        addr = 0
        if name in self.found:
            return  # Assume duplicate files (rshell, ...) are 1:1 copies
        if name in self.reserved:
            addr = self.reserved[name][0]
            self.reserved[name] = (addr, size)
        self.found[name] = Module(name, addr, size)

    def _next_address(self, size):
        if self.start_at:
            addr = (self.start_at - size - self.module_padding - 0xffff) & 0xffff0000
            self.start_at = addr
        else:
            addr = self.start_at = self.initial
        return addr

    def next_address(self, size):
        while True:
            current_start = self._next_address(size)
            current_end = current_start + size + self.module_padding
            # Is there overlap with reserved modules?
            for key, reserved in self.reserved.items():
                res_start = reserved[0]
                res_end = res_start + reserved[1] + self.module_padding
                if (res_start <= current_start <= res_end) or \
                   (res_start <= current_end <= res_end) or \
                   (current_start < res_start and current_end > res_end):
                    # We passed this reserved item, we can remove it now
                    self.start_at = min(res_start, current_start)
                    del self.reserved[key]
                    current_start = 0
                    break
            # No overlap with a reserved module?
            if current_start:
                return current_start

    def update(self, priorities):
        # sort addresses, should only contain reserved modules at this point!
        for key, reserved in self.reserved.items():
            assert reserved[1] != 0, key
        for curr in priorities:
            if not curr in self.found:
                print('# Did not find', curr, '!')
            else:
                obj = self.found[curr]
                del self.found[curr]
                if not obj.address:
                    obj.address = self.next_address(obj.size)
                self.addresses.append(obj)
        # We handled all known modules now, run over the rest we found
        for key in sorted(self.found):
            obj = self.found[key]
            obj.address = self.next_address(obj.size)
            self.addresses.append(obj)

    def gen_baseaddress(self):
        for obj in self.addresses:
            obj.gen_baseaddress()

def run_dir(target):
    print('# Generated from', target)
    print('# Generated by sdk/tools/gen_baseaddress.py')
    layout = MemoryLayout(0x7c920000)
    layout.add_reserved('user32.dll', 0x77a20000)
    for root, _, files in os.walk(target):
        for dll in [filename for filename in files if filename.endswith(ALL_EXTENSIONS)]:
            if not dll in EXCLUDE and not dll.startswith('api-ms-win-'):
                layout.add(os.path.join(root, dll), dll)
    layout.update(PRIORITIES)
    layout.gen_baseaddress()

def main(dirs):
    if len(dirs) < 1:
        trydir = os.getcwd()
        print('# No path specified, trying', trydir)
        dirs = [trydir]
    for onedir in dirs:
        run_dir(onedir)

if __name__ == '__main__':
    main(sys.argv[1:])
