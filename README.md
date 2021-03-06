# Armadillo

<p align="center">
<img src="https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fpixfeeds.com%2Fimages%2Fanimals%2Farmadillos%2F1280-148035973-armadillo-standing-up.jpg&f=1&nofb=1" width="320" height="226"/>
</p>

## Goal

Providing download links for GitHub subdirectories.

**Caution: This tool does not work reliably yet! See [Issue #2](https://github.com/dostuffthatmatters/armadillo/issues/2) for details**

<br/>

## Usage

You don't have to configure anything!

Just use/share (e.g. include in your `README`) a link in the following format:

```
https://armadillo.dostuffthatmatters.dev/{username}/{repository-name}{subdirectory-path}
```

**Armadillo** will return a `zip`-file of that subdirectory from the latest version of the default repository branch.

*When the app hasn't been used in a while the initial reponse time is approx. 5 seconds. 
After that the responses will be returned really fast. Since the infrastructure in the back
is serverless, the containers automatically shut down and boot back up in order to reduce costs.*

<br/>

Examples:

https://armadillo.dostuffthatmatters.dev/dostuffthatmatters/armadillo <br/>
https://armadillo.dostuffthatmatters.dev/dostuffthatmatters/armadillo/README.md <br/>
https://armadillo.dostuffthatmatters.dev/dostuffthatmatters/armadillo/app <br/>
https://armadillo.dostuffthatmatters.dev/dostuffthatmatters/armadillo/app/main.py <br/>

<br/>

## About the Implementation

Whenever a specific subdirectory of a repository is requested:

1. Checking the latest commit hash on the default branch
2. If a `zip`-file for that commit hash for this specific directory has not yet been generated, generate it now
3. Return that `zip`-file

_Note: The latest commit hash is always the one with respect to that subdirectory only. Meaning: When the subdirectory does not change with further commits the `zip`-file will not be regenerated as well._

<br/>
<br/>

_I am using this tool for [a university tutorial I am holding](https://github.com/dostuffthatmatters/IN8011-WS20). 
I have one repo for the whole semester with one subdirectory in it for every week.
Students should not be required to download the whole repo every week and learning/using 
git is not a programming-introductory thing!_

[_buy me a coffee :)_](https://www.buymeacoffee.com/dstm)
