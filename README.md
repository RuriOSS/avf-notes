# WIP DOCUMENT:
>[!WARNING]
> WIP
# Warning:
>[!WARNING]
> AVF vm is a good toy, a toy, but anytime before you put any important data in it, make sure you have a backup; anytime before you deploy any important service on it, make sure to at least do the stress test for a while. 
>
> AVF vm is still in early stage, and there are many things that can cause data loss or even device crash. So, please be careful when using it.
>
> It's very very not recommended to use AVF vm for any production environment.
>
> Be aware of your mental health. 
> Patience is key in life. 
> > "The vm Guest/Host panic is just like some sex play"

# Requirements:
- Rooted Android device
- Has pvmfw partition
- For some devices like Snapdragon 8 Gen 2, you might need to port pvmfw firmware yourself. It might be a long night, get some coffee and good music, and enjoy.
- For Snapdragon devices, /dev/gunyah should exist.
- For MTK devices, /dev/gzvm should exist.
- For pixel 6/6 Pro, you might need to enable pkvm in fastboot.
- For other devices like Exynos, /dev/kvm should exist.

# Introduction:
AVF (Android Virtualization Framework) is a new feature introduced in Android 14, which allows users to run virtual machines on their Android devices. But, it's not qemu-friendly, in fact, it's even crosvm-only for MediaTek devices now. And language-level memory safety does not equal to hardware-level memory safety, even not logical-level memory safety. So, at least based on my experience, it's not a production-ready feature.       
Anyway, running a full mainline Linux kernel on my Android device is exciting. I scream for it, so let's have a Waku Waku adventure!            
# For Tensor pkvm:
- Device: Pixel 7a, Tensor G2

```sh
/apex/com.android.virt/bin/crosvm run \
        --gpu-backend=virglrenderer \
        --disable-sandbox --swiotlb 64 \
        --params 'loglevel=0' --mem 4096 --cpus 8 \
        --net tap-name=$ifname \
        --initrd initrd.img --socket vm.sock \
        --block fedora.img,root vmlinux
```
# For MTK GenieZone:
- Device: Oneplus Ace 5 ultra, MTK Dimensity 9400+

```sh
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
# For Snapdragon 8 Elite:
- Device: Lenovo Y700 Gen 4, Snapdragon 8 Elite

```sh
/apex/com.android.virt/bin/crosvm --log-level debug run \
   --disable-sandbox --no-balloon --protected-vm-without-firmware --swiotlb 256 --socket vm.socket \
   --params "root=/dev/vda rw" --mem 2048 --cpus 4 \
   --net tap-name=$ifname --shared-dir /sdcard/shared:shared:type=fs \
   --block root_part,root,async-executor=epoll,sparse=false,packed-queue=true,multiple-workers=true,direct,block-size=4096 --async-executor epoll  /data/local/tmp/kernel
```

# The swiotlb game:
Seems the I/O syncing logic of crosvm is very stupid. If you write some large files to disk, like `cp /dev/zero ./test`, Explosion! Your vm crashes.      
On my device with MTK Dimensity 9400+, I can set swiotlb to 512 to mitigate the issue. But on Snapdragon 8 Elite, it will make my device crash and reboot.      
The kernel panic message on Qualcomm crashdump page is like the blazing crimson eyes of a yandere girlfriend, her voice low and chilling as she demands: "Darling...why? Why did you give her so many resources? I'm the only one who's perfect for you... I should be your one and only...exclusively..."      
So, as the kernel always says "yakimochi..." (jealousy) when running vm, seems swiotlb is max to 256M on Snapdragon 8 Elite. But with such a low swiotlb, vm will crash when writing large files. So I can only try to cast some magic spells for the start-up commands like a mahou shoujo.       
`--unmap-guest-memory-on-fork` will protect the host from crashing, but vm cannot avoid crashing with 512M swiotlb or when writing large files. And, this feature will cause guest immediate crash when mounting shared directory with virtiofs.      
If you have any idea about this, please let me know.      
# See also:
- https://github.com/Droid-VM/DroidVM
- https://github.com/polygraphene/gunyah-on-sd-guide