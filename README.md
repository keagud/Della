# Della

**Della** (named after [Perry Mason's assistant](https://en.wikipedia.org/wiki/Della_Street)) is a command line task organizer/todo list. Its basic concept is comparable to [Taskwarrior](https://taskwarrior.org/), but with the guiding philosophy that command syntax should be as simple and as close to natural language as possible. The ultimate goal is to make interactions with `della` feel more like speaking to a personal assistant than feeding input to a program.

How does this cash out? First, you can specify due dates in natural language, and `della` will figure out what you mean: 
[example]

These expressions can be arbitrarily nested, just in case that's something you need:
[example]


While you can use `della` by passing your inputs directly as command line arguments, most of its features only become apparent when using its interactive prompt, which you can start by running the program without arguements. This makes the previous examples look like this

[example]
[example]

Wowee! Colors!  This is another trick to smooth out your interactions as much as possible - if your input is invalid, you can tell before you enter it. Autocomplete also gives you feedback while you type:
[example]

That should be enough to whet your appitite. Check out [Usage](#Usage) for a detailed tour of `della`'s features.

# Install

`della` is on PyPI - install it easily with `pip`: 
```bash
$ pip install della
```

Note that `della` is designed by and for Linux users, and that's where it's intended to be used. It will *probably* work ok on MacOS, but I don't have access to a Mac to test this (if you're a Mac user, please let me know about any exotic error messages you encounter). All bets are off for Windows. 

# Usage


# Configuration


# Remote Sync

# For Developers 
Development of this project also resulted in the creation of two libraries:

  - [dateparse] is the backend for parsing natural language into dates  
  - [getchoice] is a very simple almost-clone of [pick], which I created when I was unable to find anything like it that supported text formatting a la [prompt toolkit]

They're both also available via pip, and licensed with no restrictions whatsoever for your programming pleasure. 




