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

# Requirements:
- Rooted Android device
- Has pvmfw partition
- For some devices like Snapdragon 8 Gen 2, you might need to port pvmfw firmware yourself.
- For Snapdragon devices, /dev/gunyah should exist.
- For MTK devices, /dev/gzvm should exist.
- For pixel 6/6 Pro, you might need to enable pkvm in fastboot.
- For other devices like Exynos, /dev/kvm should exist.

# For Tensor pkvm:
just run like:
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
```sh
LD_PRELOAD= /apex/com.android.virt/bin/crosvm --log-level debug run \
   --disable-sandbox --no-balloon --protected-vm-without-firmware --swiotlb 256 --socket vm.socket \
   --params "root=/dev/vda rw" --mem 2048 --cpus 4 \
   --net tap-name=$ifname --shared-dir /sdcard/shared:shared:type=fs \
   --block root_part,root,async-executor=epoll,sparse=false,packed-queue=true,multiple-workers=true,direct,block-size=4096 --async-executor epoll  /data/local/tmp/kernel
```

# The swiotlb game:
Seems the I/O logic of crosvm is very stupid. If you write a large file to disk, vm might soon crash.
On my device with MTK Dimensity 9400+, I can set swiotlb to 512 to mitigate the issue. But on Snapdragon 8 Elite, it will make device kernel panic, yes, it will make the whole device crash.       
`--unmap-guest-memory-on-fork` will protect the host from crashing, but vm will still crash when writing large files. And, this feature will cause guest immediate crash when mounting shared directory with virtiofs.      
If you have any idea about this, please let me know.      
# See also:
- https://github.com/Droid-VM/DroidVM
- https://github.com/polygraphene/gunyah-on-sd-guide