# Install on Arch Linux

The easiest and safest way to install newm is by means of its aur package which is installed as follows:

```bash
yay -S newm-git
```

## For impatient

Maybe you want to test features in development or help with debugging, whatever the case, the following tutorial aims to show how to install a different branch from the main newm branch.



1. Clone PKBUILD

```bash
yay -G newm-git
```

2. Navigate to the downloaded folder

```bash
cd newm-git
```

3. Clone pywm and newm

```bash
git clone https://github.com/jbuchermn/pywm.git --branch=<any branch>
git clone https://github.com/jbuchermn/newm.git --branch=<any branch>
```

4. Build and install

```bash
makepkg -sic
```
