# minicap-shared

This module provides the shared library used by minicap. Due to the use of private APIs, it must be built inside the AOSP source tree for each SDK level and architecture. We commit and ship prebuilt libraries inside the source tree for convenience purposes, as getting them compiled can be a major obstacle. The rest of this README assumes that you wish to compile the libraries by yourself, possibly due to trust issues and/or modifications.

## Requirements

There are several ways to set everything up and build the libraries, so we'll just cover the way we've done it. You may adjust the process however you want, but don't expect us to hold your hand if something goes wrong. Overall getting everything set up takes a considerable amount of time, with moderate skill requirements as well. It would be best if you follow the guide unless you're very confident you can do it.

### Operating system

Let's start by saying that **compiling under OS X will not work**. AOSP requires a case-sensitive file system. Furthermore, different branches of the AOSP source tree require different versions of Xcode and JDK, making the process nearly impossible. Try if you're crazy.

What we use is Linux, latest stable CoreOS to be precise. Our process relies on Docker containers to do the actual compile. The source code is copied via rsync to the Linux machine and then compiled. Any artifacts are transmitted back and added to our source tree so that normal people will not have to go through the whole process.

Using this setup, the minimum server-side machine requirements are:

* [docker](https://www.docker.com/)
* [SSH](http://www.openssh.com/)
* A user account with SSH public key authentication and sudo-less access to docker
* Approximately 20GB of disk space per checked out branch, and approximately 60GB for a full mirror. We'll get to the branches later. We recommend a 512GB SSD, possibly more if you wish to compile other things as well (i.e. not just minicap).

You'll also need [rsync](https://rsync.samba.org/) and [SSH](http://www.openssh.com/) properly set up on your development machine.

### Docker images

Pull the required docker images on the build server as follows:

```bash
docker pull openstf/aosp:jdk6
docker pull openstf/aosp:jdk7
```

These images will be used to both check out code as well as to compile it.

**A note about security:** containers created from these images currently run under the root user by default. If this is not acceptable to you, you will need to modify the `Makefile` and most of the commands below as you see fit.

### AOSP branches

Currently the following branches are required to build the libraries for all supported SDK levels and architectures:

| Branch              | SDK | Docker image to build with    |
|---------------------|-----|-------------------------------|
| android-2.3_r1      | 9   | openstf/aosp:jdk6             |
| android-2.3.3_r1    | 10  | openstf/aosp:jdk6             |
| android-4.0.1_r1    | 14  | openstf/aosp:jdk6             |
| android-4.0.3_r1    | 15  | openstf/aosp:jdk6             |
| android-4.1.1_r1    | 16  | openstf/aosp:jdk6             |
| android-4.2_r1      | 17  | openstf/aosp:jdk6             |
| android-4.3_r1      | 18  | openstf/aosp:jdk6             |
| android-4.4_r1      | 19  | openstf/aosp:jdk6             |
| android-5.0.1_r1    | 21  | openstf/aosp:jdk7             |
| android-5.1.0_r1    | 22  | openstf/aosp:jdk7             |
| android-m-preview-2 | 23  | openstf/aosp:jdk7             |

Furthermore, to make use of our provided Makefile, you should check out the branches to `/srv/aosp` for maximum ease of use.

To check out the branches, you have two options. To reduce download time and avoid bandwidth caps (on the server side), it would be advisable to fetch a full local mirror and then checkout out the individual branches from there. What tends to happen, though, is that the mirror manifest does not get updated quickly enough for new branches, and may be missing a repository or two, making it practically impossible to check out the branch you want. Additionally, the mirror takes over 50GB of disk space in addition to the checkouts.

You can also skip the mirror and download each branch directly, but that will stress the AOSP server unnecessarily.

Our recommended solution is to use a mirror and use it for all the branches you can, and if a branch fails due to a missing repo, then checkout that branch directly from the server.

### AOSP authentication

AOSP has fairly recently introduced heavy bandwidth caps on their repos. You may have to authenticate yourself [as explained](https://source.android.com/source/downloading.html#using-authentication) by the download guide. Use the link in the guide to get your `.gitcookies` file.

You'll need to put the file on your build machine. It needs to have correct permissions (i.e. `0600`) and belong to the user checking out the code. Since our process uses the root user inside the containers, make sure to set the owner and group as well.

```bash
chown root:root .gitcookies
chmod 0600 .gitcookies
```

Use sudo where required.

We will later mount this file on our containers when checking out code. Note that if you still run into bandwidth caps you may just have to wait.

### Get familiar with the checkout/build wrapper script

There are bundled helper scripts inside the docker images. To see what commands you have available, run the following command.

```bash
docker run -ti --rm openstf/aosp:jdk7 /aosp.sh help
```

### Creating an AOSP mirror

Now that we're a bit more familiar with the helper script, let's start fetching our mirror.

```bash
docker run -ti --rm \
    -v /srv/aosp/mirror:/mirror \
    -v $PWD/.gitcookies:/root/.gitcookies:ro \
    openstf/aosp:jdk7 \
    /aosp.sh create-mirror
```

This will take a LONG time, easily several hours. You may wish to leave it running overnight. If an error occurs (it will tell you), run the same command again and again until it finishes without errors.

When the command is done, you should have a copy of the latest mirror in `/srv/aosp/mirror`. We will mount this mirror when checking out individual branches.

You should rerun the command whenever a new branch you're interested in gets added to AOSP to sync the mirrored repos.

### Check out branches (using mirror)

We had a table of the needed AOSP branches earlier. The docker image for each SDK level may be different, but it should not make much difference when simply checking out code, so you should be able to use one image to check out all branches. However, if you do run into problems, you may also wish to try using the proper JDK when checking out. Check out the branch table above to see which one to use for each branch.

For each branch in the table, run the following command:

```bash
docker run -ti --rm \
    -v /srv/aosp/mirror:/mirror \
    -v /srv/aosp/android-5.1.0_r1:/aosp \
    -v $PWD/.gitcookies:/root/.gitcookies:ro \
    openstf/aosp:jdk7 \
    /aosp.sh checkout-branch android-5.1.0_r1
```

Note that the branch name is both in the mounted folder name and an option to the checkout-branch command. You have to replace both when checking out other branches.

Checking out a single branch should not take that long, perhaps 10-20 minutes per branch. Use a faster disk for better results.

Should an error occur, you can try running the command again. However, since we're using the mirror, errors shouldn't really happen. Like explained earlier, the mirror may be incomplete. If that's the case, you may have to try a direct download instead, explained next.

### Check out branches (using direct download)

For each branch you wish to download directly from the AOSP servers, run the following command:

```bash
docker run -ti --rm \
    -v /srv/aosp/android-5.1.0_r1:/aosp \
    -v $PWD/.gitcookies:/root/.gitcookies:ro \
    openstf/aosp:jdk7 \
    /aosp.sh checkout-branch --no-mirror android-5.1.0_r1
```

Note that the branch name is both in the mounted folder name and an option to the checkout-branch command. You have to replace both when checking out other branches.

Should an error occur, you can try running the command again. Depending on your luck you may have to run the command several times, and if you hit a bandwidth cap, distribute your downloads over several days.

Checking out a single branch will easily take a few hours, but it is considerably faster than setting up a full mirror.

### Saving disk space (optional)

If you're sure that you'll never need to use the Android `repo` tool on a branch you've already checked out, you can save ~40-50% of disk space by deleting the `.repo` folder inside each branch. However, be very careful not to delete the mirror's `.repo`, since you'll probably want to update it at some point in the future.

### Building

There's a `Makefile` in the `aosp` folder containing a build command for each SDK level and architecture we're interested in. If you're developing on Linux directly you may be able to `make` the libraries directly.

More likely, though, you'll actually want to use the `build-remote.sh` script at the root of the minicap repo. It's not very pretty but it works. It transmits the source code to the target machine and uses one of the docker images to run `make` inside a docker container (which is done because CoreOS doesn't come with make).

First, you'll need to tell the script where you're building.

```bash
export BUILD_HOST=core@stf-build001
```

This will be passed to SSH and rsync, and is able to benefit from your SSH config (which you must set up yourself as you like).

Now, run the build script:

```bash
./build-remote.sh
```

The first compile will take a long, long time, since it needs to compile all dependencies on the first run, for each architecture.

### Rebuilding

Any recompile after the first time will benefit from the already build dependencies and will go a lot faster, although it will still take a considerable amount of time. The `Makefile` attemps to be intelligent about which branches need to be rebuilt, but touching the common code base or the `Android.mk` file will usually require a recompile on each SDK and architecture. That by itself is reasonably fast, but setting up the AOSP build takes the most time anyway. It may take 5-15 minutes in total to do an "empty run" for each branch and architecture.

Our advice? Be damn sure your code compiles before actually compiling :)

Alternatively, you may wish to temporarily remove other targets from the `Makefile` all target when working on bigger changes but focusing on a single branch.

In any case, congratulations, you're done!
