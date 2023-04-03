# Della

**Della** (named after [Perry Mason's assistant](https://en.wikipedia.org/wiki/Della_Street)) is a command line task organizer/todo list. Its basic concept is comparable to [Taskwarrior](https://taskwarrior.org/), but with the guiding philosophy that command syntax should be as simple and as close to natural language as possible. The ultimate goal is to make interactions with `della` feel more like speaking to a personal assistant than feeding input to a program.

How does this cash out? First, you can specify due dates in natural language, and `della` will figure out what you mean: 
![1](screenshots/della-1.png)

These expressions can be arbitrarily nested, just in case that's something you need:

![2](screenshots/della-2.png)

While you can use `della` by passing your inputs directly as command line arguments, most of its features only become apparent when using its interactive prompt, which you can start by running the program without arguements. This makes the previous examples look like this

![3](screenshots/della-3.png)
![4](screenshots/della-4.png)

Wowee! Colors!  This is another trick to smooth out your interactions as much as possible - if your input is invalid, you can tell before you enter it. Autocomplete also gives you feedback while you type:

![5](screenshots/della-5.png)

That should be enough to whet your appetite. For a crash course in usage and a list of all available commands type `@help` at the interactive prompt

# Install

`della` is on PyPI - install it easily with `pip`: 
```bash
$ pip install della
```

Note that support for non-GNU/Linux operating systems is not guaranteed. It will *probably* work ok on MacOS, but I don't have access to a Mac to test this (if you're a Mac user, please let me know about any exotic error messages you encounter). All bets are off for Windows. 


# Configuration

When run for the first time, `della` creates a config file at `$USER_HOME/.config/della/config.toml`. On each subsequent startup, it will read from this file to set options user options. The starting config file is commented to help you tweak it to your liking.

# Remote Sync
`della` can keep your tasks in sync over multiple devices using SSH. 

Why do you you need to provide your own hosting? Two reasons:
1. If I provided a hosted database, that would go way over my budget for this project (which is $0.00; [I'm unemployed currently](https://github.com/keagud/resume))
2. I don't want your data. Why do people keep giving me their data? I never ask for it, yet people keep giving it to me. 

Setting up a remote host for syncing is very simple; all you need is a working ssh login to some sort of POSIX-ish machine. You don't even need to install anything special on the remote! The "remote" section of the default generated config file contains more details on configuration.


# For Developers 
Development of this project also resulted in the creation of two libraries:

  - [dateparse](https://github.com/keagud/dateparse) is the backend for parsing natural language into dates  
  - [getchoice](https://github.com/keagud/getchoice) is a very simple almost-clone of [pick], which I created when I was unable to find anything like it that supported text formatting a la [prompt toolkit]

They're both also available via pip, and licensed with no restrictions whatsoever. 


