# elm-test-runner


Only run and compile some test files at a time. Only rules are that you need to expose `spec : Test` in any files you want to have things run from.

![screen shot 2016-09-03 at 06 30 41](https://cloud.githubusercontent.com/assets/1139198/18222822/a9f72352-71a3-11e6-834f-c47d838a06d5.png)
![screen shot 2016-09-03 at 06 52 38](https://cloud.githubusercontent.com/assets/1139198/18222821/a9f5f342-71a3-11e6-886d-839dca279b46.png)
![screen shot 2016-09-03 at 06 53 26](https://cloud.githubusercontent.com/assets/1139198/18222823/a9f7372a-71a3-11e6-82c3-842608900dad.png)


```
usage: run_single_elm_test.py [-h] [--module] [--root ROOT] [--bin BIN]
                              [--output OUTPUT]
                              spec_file [spec_file ...]
```
Run tests in files manually by just giving their name. Give multiple names if you want. Globs too.

Using the `--module` flag will create a test suite generated from every module that imports that module.
```
This script will:
    - Grab the files
    - Find the exposed names from a file
    - Group all the ones with the type `: Test` or the name `spec`
    - Create a test suite composed from all the found tests in each file
    - Run them!

positional arguments:
  spec_file        give relative path to the spec file you want to run or the name of the module

optional arguments:
  -h, --help       show this help message and exit
  --module         use a module name
  --root ROOT      define the root folder where your elm-package lives
  --bin BIN        define a custom binary location - if none provided, default to global
  --output OUTPUT  define a custom output file
```
