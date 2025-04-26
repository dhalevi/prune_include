# prune_include

A brute force approach to find and remove all redundant `#include` directives in a project.  

## Inspiration

I had to maintain a large, full of history code base.
The compilation took forever...

One of the reasons was that over time, more an more #include directives  
were added to the coede (in headers as well as source files) and these caused:

1. Longer compile time per file
2. Way too much dependency in the project

Solution: remove un-needed #include from the project.
 
Looking for previous such solutions, I stubled upon this thread:  
https://stackoverflow.com/questions/614794/detecting-superfluous-includes-in-c-c  
And from there:  
https://github.com/cognitivewaves/misc/tree/master/check-header-includes

It did a great job, but was not easy to set-up.

So, I came up with this script.

Yes, it is brute force. 
It assume that a 'build' on given project will produce an 'artifact'
It is (I think) easily configurable.

## Method

- Validate project build produce an artifact file.
- For each source file in a project:
  - Remove artifact
  - comment next `#include` directive
  - build project and look for the artifact.
  - if the build failed, restore the directive and try the next one
  - otherwise (build OK) - repeat for the next directive/file
  
## Example

From this repo, assuming g++ works:

```sh
python prune_include.py  --build "g++ test\hello.cpp" .
```
