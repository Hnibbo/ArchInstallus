#!/usr/bin/env python3
"""
ArchInstallus PC Companion Tool
Communicates with Flipper Zero to perform REAL Arch Linux installation
"""

import usb.core
import usb.util
import time
import sys
import os
from typing import Tuple, Optional

class ArchInstallusPC:
    """PC-side companion for Flipper Zero ArchInstallus app"""
    
    # USB Configuration
    VENDOR_ID = 0x0483  # STMicroelectronics (Flipper Zero)
    PRODUCT_ID = 0x5720  # Flipper Zero
    INTERFACE_NUMBER = 0
    ENDPOINT_OUT = 0x01
    ENDPOINT_IN = 0x81
    
    # Command definitions
    CMD_HELLO = 0x01
    CMD_DETECT_DISKS = 0x02
    CMD_PARTITION = 0x03
    CMD_FORMAT = 0x04
    CMD_MOUNT = 0x05
    CMD_DOWNLOAD = 0x06
    CMD_INSTALL = 0x07
    CMD_CONFIGURE = 0x08
    CMD_FINISH = 0x09
    CMD_STATUS = 0x0A
    CMD_ERROR = 0xFF
    
    def __init__(self):
        self.device = None
        self.connected = False
    
    def connect(self) -> bool:
        """Connect to Flipper Zero via USB"""
        try:
            self.device = usb.core.find(idVendor=self.VENDOR_ID, idProduct=self.PRODUCT_ID)
            if self.device is None:
                print("❌ Flipper Zero not found!")
                return False
            
            # Set configuration
            self.device.set_configuration()
            
            # Claim interface
            usb.util.claim_interface(self.device, self.INTERFACE_NUMBER)
            
            self.connected = True
            print("✅ Connected to Flipper Zero")
            return True
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def send_command(self, command: int, data: str = "") -> bool:
        """Send command to Flipper Zero"""
        if not self.connected:
            return False
        
        try:
            # Format command packet
            packet = f"{command:02X}{data}".encode('ascii')
            self.device.write(self.ENDPOINT_OUT, packet)
            return True
        except Exception as e:
            print(f"❌ Send failed: {e}")
            return False
    
    def receive_response(self) -> Optional[Tuple[int, int, int, str]]:
        """Receive response from Flipper Zero"""
        if not self.connected:
            return None
        
        try:
            # Read response
            data = self.device.read(self.ENDPOINT_IN, 1024)
            
            if len(data) >= 9:  # Minimum response size
                command = data[0]
                status = int.from_bytes(data[1:5], 'little')
                progress = int.from_bytes(data[5:9], 'little')
                response_data = data[9:].decode('ascii', errors='ignore')
                
                return (command, status, progress, response_data)
            
        except Exception as e:
            print(f"❌ Receive failed: {e}")
        
        return None
    
    def hello(self) -> bool:
        """Initialize connection with Flipper Zero"""
        if self.send_command(self.CMD_HELLO, "PC_READY"):
            response = self.receive_response()
            return response and response[1] == 0
        return False
    
    def detect_disks(self) -> list:
        """Detect available disks"""
        print("🔍 Detecting available disks...")
        if self.send_command(self.CMD_DETECT_DISKS):
            response = self.receive_response()
            if response and response[1] == 0:
                disks = response[3].split(';')
                print(f"✅ Found {len(disks)} disk(s): {disks}")
                return disks
        return []
    
    def partition_disk(self, disk_path: str, partitions: str) -> bool:
        """Partition the specified disk"""
        print(f"📋 Partitioning {disk_path} with {partitions}")
        if self.send_command(self.CMD_PARTITION, f"{disk_path}:{partitions}"):
            while True:
                response = self.receive_response()
                if not response:
                    return False
                
                if response[1] == 0:  # Success
                    print("✅ Partitioning complete")
                    return True
                elif response[1] == 1:  # Progress
                    print(f"⏳ Partitioning: {response[2]}%")
                    time.sleep(0.5)
                else:  # Error
                    print(f"❌ Partitioning failed: {response[3]}")
                    return False
        return False
    
    def format_partitions(self, formats: str) -> bool:
        """Format partitions"""
        print(f"💾 Formatting partitions: {formats}")
        if self.send_command(self.CMD_FORMAT, formats):
            while True:
                response = self.receive_response()
                if not response:
                    return False
                
                if response[1] == 0:  # Success
                    print("✅ Formatting complete")
                    return True
                elif response[1] == 1:  # Progress
                    print(f"⏳ Formatting: {response[2]}%")
                    time.sleep(0.5)
                else:  # Error
                    print(f"❌ Formatting failed: {response[3]}")
                    return False
        return False
    
    def mount_filesystems(self, mounts: str) -> bool:
        """Mount filesystems"""
        print(f"📁 Mounting filesystems: {mounts}")
        if self.send_command(self.CMD_MOUNT, mounts):
            response = self.receive_response()
            if response and response[1] == 0:
                print("✅ Mounting complete")
                return True
        return False
    
    def download_arch(self, mirror: str) -> bool:
        """Download Arch Linux base system"""
        print(f"⬇️ Downloading Arch Linux from {mirror}")
        if self.send_command(self.CMD_DOWNLOAD, mirror):
            while True:
                response = self.receive_response()
                if not response:
                    return False
                
                if response[1] == 0:  # Success
                    print("✅ Download complete")
                    return True
                elif response[1] == 1:  # Progress
                    print(f"⏳ Downloading: {response[2]}%")
                    time.sleep(1)
                else:  # Error
                    print(f"❌ Download failed: {response[3]}")
                    return False
        return False
    
    def install_system(self, packages: str) -> bool:
        """Install Arch Linux system"""
        print(f"⚙️ Installing packages: {packages}")
        if self.send_command(self.CMD_INSTALL, packages):
            while True:
                response = self.receive_response()
                if not response:
                    return False
                
                if response[1] == 0:  # Success
                    print("✅ Installation complete")
                    return True
                elif response[1] == 1:  # Progress
                    print(f"⏳ Installing: {response[2]}%")
                    time.sleep(1)
                else:  # Error
                    print(f"❌ Installation failed: {response[3]}")
                    return False
        return False
    
    def configure_system(self, config: str) -> bool:
        """Configure installed system"""
        print(f"🔧 Configuring system: {config}")
        if self.send_command(self.CMD_CONFIGURE, config):
            while True:
                response = self.receive_response()
                if not response:
                    return False
                
                if response[1] == 0:  # Success
                    print("✅ Configuration complete")
                    return True
                elif response[1] == 1:  # Progress
                    print(f"⏳ Configuring: {response[2]}%")
                    time.sleep(0.5)
                else:  # Error
                    print(f"❌ Configuration failed: {response[3]}")
                    return False
        return False
    
    def perform_installation(self) -> bool:
        """Perform complete Arch Linux installation"""
        print("🚀 Starting REAL Arch Linux installation...")
        
        # Step 1: Initialize
        if not self.hello():
            return False
        
        # Step 2: Detect disks
        disks = self.detect_disks()
        if not disks:
            print("❌ No disks detected")
            return False
        
        primary_disk = disks[0]  # Use first detected disk
        
        # Step 3: Partition disk
        if not self.partition_disk(primary_disk, "512M:2G:4G:remain"):
            return False
        
        # Step 4: Format partitions
        if not self.format_partitions("ext4:/dev/sda1;btrfs:/dev/sda2"):
            return False
        
        # Step 5: Mount filesystems
        if not self.mount_filesystems("/dev/sda1:/mnt;/dev/sda2:/mnt/home"):
            return False
        
        # Step 6: Download Arch Linux
        if not self.download_arch("https://mirror.rackspace.com/archlinux"):
            return False
        
        # Step 7: Install base system
        if not self.install_system("base,base-devel,linux,networkmanager"):
            return False
        
        # Step 8: Configure system
        if not self.configure_system("archinstallus,UTC,en_US.UTF-8"):
            return False
        
        print("🎉 REAL Arch Linux installation completed!")
        return True
    
    def disconnect(self):
        """Disconnect from Flipper Zero"""
        if self.device:
            try:
                usb.util.release_interface(self.device, self.INTERFACE_NUMBER)
                self.connected = False
                print("📴 Disconnected from Flipper Zero")
            except:
                pass

def main():
    """Main function"""
    archinstallus = ArchInstallusPC()
    
    print("🔗 ArchInstallus PC Companion Tool")
    print("This tool performs REAL Arch Linux installation via Flipper Zero")
    print()
    
    # Connect to Flipper Zero
    if not archinstallus.connect():
        print("❌ Failed to connect to Flipper Zero")
        print("Make sure the Flipper Zero is connected via USB and has ArchInstallus app running")
        sys.exit(1)
    
    try:
        # Perform installation
        success = archinstallus.perform_installation()
        
        if success:
            print("✅ Installation successful! Arch Linux is now installed on the target system.")
        else:
            print("❌ Installation failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ Installation cancelled by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    finally:
        archinstallus.disconnect()

if __name__ == "__main__":
    main()
