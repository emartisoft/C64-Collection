#!/usr/bin/env python3
# ===================================================================================
# Project:   DumpMaster64 - Python Script - Disk Tools Library
# Version:   v1.1
# Year:      2022
# Author:    Stefan Wagner
# Github:    https://github.com/wagiminator
# License:   http://creativecommons.org/licenses/by-sa/3.0/
# ===================================================================================
#
# Description:
# ------------
# Basic functions to work with disks
#
# References:
# -----------
# - PETSCII/ASCII table from https://github.com/AndiB/PETSCIItoASCII
#
# Dependencies:
# -------------
# None


# ===================================================================================
# BAM Class - Working with the BAM
# ===================================================================================

class BAM:
    def __init__(self, bam):
        self.bam = bam

    # Get disk name
    def getdiskname(self):
        return PETtoASC(PETdelpadding(self.bam[0x90:0xA0]))

    # Get disk ID
    def getdiskident(self):
        return PETtoASC(self.bam[0xA2:0xA4])

    # Generate header for directory
    def getheader(self):
        header  = '0    \"'
        header += (self.getdiskname() + '\"').ljust(19)
        header += self.getdiskident().ljust(3)
        header += PETtoASC(self.bam[0xA5:0xA7])
        return header.upper()

    # Calculate free blocks shown in directory (exclude track 18)
    def getblocksfree(self):
        blocksfree = 0
        for x in range(0x04, 0x90, 0x04): 
            if not x == 0x48: blocksfree += self.bam[x]
        return blocksfree

    # Get total number of allocated sectors on disk
    def getallocated(self):
        allocated = 0
        for x in range(0x04, 0x90, 0x04): 
            allocated += (getsectors(x // 4) - self.bam[x])
        return allocated

    # Check if specified sector on specified track is free (not allocated)
    def blockisfree(self, track, sector):
        return self.bam[4 * track + 1 + (sector // 8)] & (1 << (sector % 8)) > 0

    # Allocate a block in the BAM
    def allocateblock(self, track, sector):
        temp  = self.bam[4 * track + 1 + (sector // 8)]
        temp &= 255 - (1 << (sector % 8))
        self.bam[4 * track + 1 + (sector // 8)] = temp

    # De-allocate a block in the BAM
    def deallocateblock(self, track, sector):
        temp  = self.bam[4 * track + 1 + (sector // 8)]
        temp |= (1 << (sector % 8))
        self.bam[4 * track + 1 + (sector // 8)] = temp


# ===================================================================================
# DIR Class - Working with the Directory
# ===================================================================================

class Dir:
    def __init__(self, dirblocks):
        self.bam = BAM(dirblocks[:256])
        self.dir = dirblocks[256:]
        self.dirpass()

    def dirpass(self):
        self.title      = self.bam.getdiskname()
        self.ident      = self.bam.getdiskident()
        self.blocksfree = self.bam.getblocksfree()
        self.header     = self.bam.getheader()
        self.filelist   = list()
        for ptr in range(len(self.dir) // 0x20):
            base = 0x20 * ptr
            if self.dir[base+0x02] > 0:
                file = dict()
                file['base']    = base
                file['type']    = FILETYPES[self.dir[base+0x02] & 0x07]
                file['locked']  = ((self.dir[base+0x02] & 0x40) > 0)
                file['closed']  = ((self.dir[base+0x02] & 0x80) > 0)
                file['track']   = self.dir[base+0x03]
                file['sector']  = self.dir[base+0x04]
                file['name']    = PETtoASC(PETdelpadding(self.dir[base+0x05:base+0x15]))
                file['size']    = int.from_bytes(self.dir[base+0x1E:base+0x20], byteorder='little')
                self.filelist.append(file)


# ===================================================================================
# Basic Functions to work with a Disk
# ===================================================================================

# Get number of sectors in track
def getsectors(track):
    if track <  1:  return 0
    if track < 18:  return 21
    if track < 25:  return 19
    if track < 31:  return 18
    if track < 41:  return 17
    return 0

# Get absolute sector number
def getsectornumber(track, sector):
    number = 0
    for x in range(1, track):
        number += getsectors(x)
    return number + sector

# Get pointer to track/sector in D64 file
def getfilepointer(track, sector):
    return 256 * getsectornumber(track, sector)


# ===================================================================================
# PETSCII Functions
# ===================================================================================

# Convert PETSCII bytes to ASCII string
def PETtoASC(line):
    result = ''
    for x in line:
        result += chr(PETtoASCtable[x])
    return result

# Convert ASCII string to PETSCII string
def ASCtoPET(line):
    result = ''
    for x in line:
        result += chr(ASCtoPETtable[ord(x)])
    return result

# Delete $A0 padding in PETSCII bytes
def PETdelpadding(line):
    result = b''
    for x in line:
        if not x == 0xA0:
              result += bytes([x])
    return result

# Remove character invalid for filenames
def cleanstring(filename):
    filename = filename.lstrip().rstrip().replace(' ', '_')
    return ''.join(c for c in filename if c.isalnum() or c=='_' or c=='-')


# ===================================================================================
# PETSCII to ASCII Conversion Tables - from https://github.com/AndiB/PETSCIItoASCII
# ===================================================================================

# PETSCII to ASCII conversion table
PETtoASCtable = [
    0x00,0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x14,0x09,0x0d,0x11,0x93,0x0a,0x0e,0x0f,
    0x10,0x0b,0x12,0x13,0x08,0x15,0x16,0x17,0x18,0x19,0x1a,0x1b,0x1c,0x1d,0x1e,0x1f,
    0x20,0x21,0x22,0x23,0x24,0x25,0x26,0x27,0x28,0x29,0x2a,0x2b,0x2c,0x2d,0x2e,0x2f,
    0x30,0x31,0x32,0x33,0x34,0x35,0x36,0x37,0x38,0x39,0x3a,0x3b,0x3c,0x3d,0x3e,0x3f,
    0x40,0x61,0x62,0x63,0x64,0x65,0x66,0x67,0x68,0x69,0x6a,0x6b,0x6c,0x6d,0x6e,0x6f,
    0x70,0x71,0x72,0x73,0x74,0x75,0x76,0x77,0x78,0x79,0x7a,0x5b,0x5c,0x5d,0x5e,0x5f,
    0xc0,0xc1,0xc2,0xc3,0xc4,0xc5,0xc6,0xc7,0xc8,0xc9,0xca,0xcb,0xcc,0xcd,0xce,0xcf,
    0xd0,0xd1,0xd2,0xd3,0xd4,0xd5,0xd6,0xd7,0xd8,0xd9,0xda,0xdb,0xdc,0xdd,0xde,0xdf,
    0x80,0x81,0x82,0x83,0x84,0x85,0x86,0x87,0x88,0x89,0x8a,0x8b,0x8c,0x8d,0x8e,0x8f,
    0x90,0x91,0x92,0x0c,0x94,0x95,0x96,0x97,0x98,0x99,0x9a,0x9b,0x9c,0x9d,0x9e,0x9f,
    0xa0,0xa1,0xa2,0xa3,0xa4,0xa5,0xa6,0xa7,0xa8,0xa9,0xaa,0xab,0xac,0xad,0xae,0xaf,
    0xb0,0xb1,0xb2,0xb3,0xb4,0xb5,0xb6,0xb7,0xb8,0xb9,0xba,0xbb,0xbc,0xbd,0xbe,0xbf,
    0x60,0x41,0x42,0x43,0x44,0x45,0x46,0x47,0x48,0x49,0x4a,0x4b,0x4c,0x4d,0x4e,0x4f,
    0x50,0x51,0x52,0x53,0x54,0x55,0x56,0x57,0x58,0x59,0x5a,0x7b,0x7c,0x7d,0x7e,0x7f,
    0xa0,0xa1,0xa2,0xa3,0xa4,0xa5,0xa6,0xa7,0xa8,0xa9,0xaa,0xab,0xac,0xad,0xae,0xaf,
    0xb0,0xb1,0xb2,0xb3,0xb4,0xb5,0xb6,0xb7,0xb8,0xb9,0xba,0xbb,0xbc,0xbd,0xbe,0xbf]


# ASCII to PETSCII conversion table
ASCtoPETtable = [
    0x00,0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x14,0x20,0x0d,0x11,0x93,0x0a,0x0e,0x0f,
    0x10,0x0b,0x12,0x13,0x08,0x15,0x16,0x17,0x18,0x19,0x1a,0x1b,0x1c,0x1d,0x1e,0x1f,
    0x20,0x21,0x22,0x23,0x24,0x25,0x26,0x27,0x28,0x29,0x2a,0x2b,0x2c,0x2d,0x2e,0x2f,
    0x30,0x31,0x32,0x33,0x34,0x35,0x36,0x37,0x38,0x39,0x3a,0x3b,0x3c,0x3d,0x3e,0x3f,
    0x40,0xc1,0xc2,0xc3,0xc4,0xc5,0xc6,0xc7,0xc8,0xc9,0xca,0xcb,0xcc,0xcd,0xce,0xcf,
    0xd0,0xd1,0xd2,0xd3,0xd4,0xd5,0xd6,0xd7,0xd8,0xd9,0xda,0x5b,0x5c,0x5d,0x5e,0x5f,
    0xc0,0x41,0x42,0x43,0x44,0x45,0x46,0x47,0x48,0x49,0x4a,0x4b,0x4c,0x4d,0x4e,0x4f,
    0x50,0x51,0x52,0x53,0x54,0x55,0x56,0x57,0x58,0x59,0x5a,0xdb,0xdc,0xdd,0xde,0xdf,
    0x80,0x81,0x82,0x83,0x84,0x85,0x86,0x87,0x88,0x89,0x8a,0x8b,0x8c,0x8d,0x8e,0x8f,
    0x90,0x91,0x92,0x0c,0x94,0x95,0x96,0x97,0x98,0x99,0x9a,0x9b,0x9c,0x9d,0x9e,0x9f,
    0xa0,0xa1,0xa2,0xa3,0xa4,0xa5,0xa6,0xa7,0xa8,0xa9,0xaa,0xab,0xac,0xad,0xae,0xaf,
    0xb0,0xb1,0xb2,0xb3,0xb4,0xb5,0xb6,0xb7,0xb8,0xb9,0xba,0xbb,0xbc,0xbd,0xbe,0xbf,
    0x60,0x61,0x62,0x63,0x64,0x65,0x66,0x67,0x68,0x69,0x6a,0x6b,0x6c,0x6d,0x6e,0x6f,
    0x70,0x71,0x72,0x73,0x74,0x75,0x76,0x77,0x78,0x79,0x7a,0x7b,0x7c,0x7d,0x7e,0x7f,
    0xe0,0xe1,0xe2,0xe3,0xe4,0xe5,0xe6,0xe7,0xe8,0xe9,0xea,0xeb,0xec,0xed,0xee,0xef,
    0xf0,0xf1,0xf2,0xf3,0xf4,0xf5,0xf6,0xf7,0xf8,0xf9,0xfa,0xfb,0xfc,0xfd,0xfe,0xff]


# ===================================================================================
# Various Constants
# ===================================================================================

# Filetypes
FILETYPES = ['DEL', 'SEQ', 'PRG', 'USR', 'REL']