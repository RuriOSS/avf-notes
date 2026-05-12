# Warning:

>[!WARNING]
> This document is last edited on May 2026, based on android 16. Some information in this document might be outdated.
>
> Seems the version of crosvm is always 0.1.0, so I used crosvm in com.android.virt on my device to write this doc. 
>
> Different firmware/crosvm version can make many issues unreproducible, you have to test the things yourself.
>
> I'm not a vm/hw developer, be careful of wrong information, and feel free to correct me or make a pull request.


>[!WARNING]
> Anytime before you put any important data in your vm, make sure you have a backup; anytime before you deploy any important service on it, make sure to at least do the stress test for a while.       
>
> AVF is still in early stage, and there are many things that can cause data loss or device crash. So, please be careful when using it.
>
> Be aware of your mental health.       
> Patience is key in life.       
> > "Tons of vm Guest/Host panic is just like a sex play"
# Introduction:
This is a note contains some info of running virtual machines on Android devices with AVF. Just some notes based on my experience, and I hope it can be helpful for you.         
And, please read [gunyah-on-sd-guide](https://github.com/polygraphene/gunyah-on-sd-guide) before you start, It contains many useful information.          
# Requirements:
- Rooted Android device
- Has pvmfw partition
- For some devices like Snapdragon 8 Gen 2, you might need to port pvmfw firmware yourself.
- For Snapdragon devices, /dev/gunyah should exist.
- For MTK devices, /dev/gzvm should exist.
- For pixel 6/6 Pro, you might need to enable pkvm in fastboot.
- For other devices, /dev/kvm should exist.

# Background:
AVF (Android Virtualization Framework) is a new feature introduced in Android 14, which allows users to run virtual machines on their Android devices.

But, AVF used a new virtualization backend written in rust, the crosvm. Rust is not a silver bullet. As we know, language-level memory safety does not equal to hardware-level memory safety, even not logical-level memory safety. So at least based on my experience, it's not a production-ready feature.       


Anyway, running a full mainline Linux kernel on my Android device is exciting. I scream for it, so let's have a Waku Waku adventure!           
# Mounting rootfs:
Loop mounting an image is the most common way to edit/prepare rootfs for vm, like:
```sh
mkdir rootfs
LOOP_DEV=$(losetup -f)
losetup $LOOP_DEV root_part
mount $LOOP_DEV ./rootfs
```
On some devices, loop mounting an image is banned by SELinux, for example Oneplus Ace 5 Ultra.       
If you cannot loop-mount your rootfs properly, try `setenforce 0`(Dangerous!!! Do it if you really know what you're doing), try editing SELinux policies, try to make rootfs on another device, or try to migrate tarball from erofs in vm.      
# Tensor pkvm:
- Pixel 7a
- Tensor G2
- Android 16
### Start-up command:
```sh
ulimit -l unlimited
unset LD_PRELOAD
/apex/com.android.virt/bin/crosvm run \
        --gpu-backend=virglrenderer \
        --disable-sandbox --swiotlb 64 \
        --params 'loglevel=0' --mem 4096 --cpus 8 \
        --net tap-name=crosvm_tap \
        --initrd initrd.img --socket vm.sock \
        --block fedora.img,root vmlinux
```
### note:
You'll have the best experience on Tensor chips, with general pkvm support and always up-to-date firmware maintenance.         
As AVF/crosvm is developed by Google, it will be more stable and better optimized.         
With the latest GrapheneOS, android 16, official Terminal app can even have display output in vm.      
# MTK GenieZone:
- Oneplus Ace 5 ultra
- MTK Dimensity 9400+
- Android 16
### Start-up command:
```sh
ulimit -l unlimited
unset LD_PRELOAD
/apex/com.android.virt/bin/crosvm run \
    --disable-sandbox \
    --protected-vm-without-firmware \
    --swiotlb 512 \
    --params 'loglevel=4 root=/dev/vda rw' \
    --shared-dir /sdcard/shared:shared:type=fs \
    --mem 8192 --cpus 4 \
    --net tap-name=crosvm_tap \
    --socket vm.sock \
    --vsock 3 \
    --initrd initrd.img \
    --block debian.img,root \
    vmlinuz
```
### NOTE:
- MTK GenieZone does not have qemu support.
- 512M swiotlb is required to avoid vm crash when writing large files to disk.
- If you lower the swiotlb to 64M (default value), good luck to you. On my device, disk I/O will be very unstable.

# Snapdragon Gunyah:
- Lenovo Y700 Gen 4
- Snapdragon 8 Elite
- Android 16
### Start-up command:
```sh
ulimit -l unlimited
unset LD_PRELOAD
/apex/com.android.virt/bin/crosvm --log-level debug run \
   --disable-sandbox --no-balloon --protected-vm-without-firmware \
   --swiotlb 256 --socket vm.socket \
   --params "root=/dev/vda rw" --mem 2048 --cpus 4 \
   --net tap-name=crosvm_tap --shared-dir /sdcard/shared:shared:type=fs \
   --block root_part,root,async-executor=epoll,sparse=false,packed-queue=true,multiple-workers=true,direct,block-size=4096 \
   --async-executor epoll  /data/local/tmp/kernel
```
### NOTE:
- You might get better experience with qemu, but I didn't test it.
- swiotlb is max to 256M on my device, or it will cause device crash and reboot.
- It's the most unstable one among the three when using original /apex/com.android.virt/bin/crosvm on my device.
- You can try [DroidVM](https://github.com/Droid-VM/DroidVM), seems they are working for Snapdragon gunyah, and did many hacks to make it work.

# Networking Magic:
## For wifi networks:
Just see [gunyah-on-sd-guide](https://github.com/polygraphene/gunyah-on-sd-guide), in Networking section, you can find the instructions to set up tap interface for your vm.       
## For mobile data:
I really remember that I have seen a tutorial about that, using gvisor-tap-vsock. [This article](https://temofeev.ru/info/articles/zapusk-linux-na-ustroystvakh-android-bez-podderzhki-avf/) also mentioned that, but I cannot find it now.      
I have write a simple script for it before, just as proof-of-concept, so based on that script:
```sh
ifname=crosvm_tap
if [ ! -d /sys/class/net/$ifname ]; then
  # https://crosvm.dev/book/devices/net.html
  ip tuntap add mode tap user root vnet_hdr crosvm_tap
  ip addr add 192.168.10.1/24 dev crosvm_tap
  ip link set crosvm_tap up

  # routing
  sysctl net.ipv4.ip_forward=1
  HOST_DEV=$(ip route get 8.8.8.8 | awk -- '{printf $5}')
  iptables -t nat -A POSTROUTING -o "${HOST_DEV}" -j MASQUERADE
  iptables -A FORWARD -i "${HOST_DEV}" -o crosvm_tap -m state --state RELATED,ESTABLISHED -j ACCEPT
  iptables -A FORWARD -i crosvm_tap -o "${HOST_DEV}" -j ACCEPT

  # the main route table needs to be added
  ip rule add from all lookup main pref 1
fi
rm ../network.sock
killall -9 gvproxy
gvproxy -listen vsock://:1024 -listen unix://$(pwd)/../network.sock &
sleep 2
curl --unix-socket /data/data/com.termux/files/home/network.sock http:/unix/services/forwarder/expose -X POST -d '{"local":":22","remote":"192.168.127.2:22"}'
```
Remember to add `--vsock 3` and `--net tap-name=crosvm_tap` in crosvm start-up cmdline. And then, in vm:
```sh
apt install -y netplan.io
cat <<EOF > /etc/netplan/90-default.yaml
network:
    version: 2
    ethernets:
all-en:
    match:
name: en*
    dhcp4: false

    addresses:
      - 192.168.10.2/24
    routes:
      - to: default
via: 192.168.10.1
    nameservers:
  addresses: [8.8.8.8]
    dhcp6: true
    dhcp6-overrides:
use-domains: true
all-eth:
    match:
name: eth*
    dhcp4: true
    dhcp4-overrides:
use-domains: true
    dhcp6: true
    dhcp6-overrides:
use-domains: true
EOF
```
Then:
```sh
ip route del default
ip addr add 192.168.10.2/24 dev enp0s2
ip link set enp0s2 up
gvforwarder >/dev/null 2>&1 &
sleep 2
ip route add default via 192.168.127.1
```
### NOTE:
- Compile gvisor-tap-vsock yourself, and also copy it to your vm.
- I should apologize that I really cannot find the original tutorial, If you have it, please let me know.


# Swiotlb GalGame:
>[!WARNING]
>Based on my experience on Android 16, May 12 2026. Be aware of outdated information or device/firmware differences.

Seems the I/O syncing logic of crosvm is crazy. If you write some large files to disk, like `cp /dev/zero ./test`, Explosion! Your vm crashes.      

On my device with MTK Dimensity 9400+, I can set swiotlb to 512M to mitigate the issue. But on Snapdragon 8 Elite, it will make my device crash and reboot.      


> The kernel panic message on Qualcomm crashdump page is like the blazing crimson eyes of a yandere girlfriend, her voice low and chilling as she demands: "Darling...why? Why did you give her so many resources? I'm the only one who's perfect for you... I should be your one and only...exclusively..."      

So, as the kernel always says "yakimochi..." (jealousy) when running vm, seems swiotlb is max to 256M on Snapdragon 8 Elite. But with such a low swiotlb, vm will crash when writing large files. So I can only try to write some magic spells for the start-up commands, like a mahou shoujo :<       

`--unmap-guest-memory-on-fork` will protect the host from crashing, but vm cannot avoid crashing with 512M swiotlb or when writing large files. And, this feature will cause guest immediate crash when mounting shared directory with virtiofs.      

Even with 256M large swiotlb and only 2048M memory, disk I/O in vm is unstable after my device has 21 hours uptime. 1024M is also sometimes unstable now, seems 512M is okey, test it yourself.     
> "Everything is I/O on Linux, when I/O's unstable, everything is cooked..."

In one word, it's okey for a testing environment, but you'd better do not use it to deploy a service.     

I also tried to compile the latest crosvm, minijail is a superhell, it cannot be linked properly in termux. I tried to just disable all default features and compile only the core, crosvm works, but all the problem still exists as before.            
### Possible solutions:
- Set 512M swiotlb, if you use MTK device.
- Switch to Pixel with Tensor, and get the latest firmware.
- Set 256M swiotlb with low memory like 2048M, and pray.
- Wait for official fix for your device.
- Try DroidVM, or maybe QEMU.

Or if you have any idea, please let me know.
### See also:
https://github.com/polygraphene/gunyah-on-sd-guide/issues/14      
I have also wrote about the disk I/O problem here.   
# CPU Core Stats:
Based on my experience, the more cpu cores you give to vm, the more unstable it will be.       
Most of the time, 4 cores is the best choice, and 8 cores will randomly cause vm crash.        
It can be different on your device, so test it yourself.      
# Performance Cosplay:
In the vm, you'll see crazy disk I/O speed high to Gbps level, every block is hanging in cache, waiting to just have a savage oom.          
You'll also see very low pipe-based context switch speed.        
So don't be surprised if you see the weird performance in vm, it's just a cosplay.        

If you have any idea to improve this issue, please let me know.
# About the author:
- [Moe Hakozaki](https://github.com/Moe-hacker) in [RuriOSS](https://github.com/RuriOSS)    

"Devices Have Limits, But Tech Doesn't"
# See also:
- https://github.com/Droid-VM/DroidVM
- https://github.com/polygraphene/gunyah-on-sd-guide