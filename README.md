# Armadillo

<img align="right" src="https://www.nationalgeographic.com/content/dam/animals/thumbs/rights-exempt/mammals/group/armadillos_thumb.JPG" width="200" height="200"/>

### Goal

Providing download links for GitHub subdirectories.

<br/>

### Usecase

You might be looking at reference projects to be deployed on some Cloud Infrastructure (e.g. GCP). They have a GitHub repository containing these examples @ [.../GoogleCloudPlatform/cloud-code-samples](https://github.com/GoogleCloudPlatform/cloud-code-samples).

I only want to read into the project located @ [/python/django/python-hello-world](https://github.com/GoogleCloudPlatform/cloud-code-samples/tree/master/python/django/python-hello-world).

**The Problem:** I can only download the code either file by file or by cloning the whole repository ... not great!

**The Solution:** Now I can use **Armadillo** to do that for me. The following link does just that:
[https://armadillo.dostuffthatmatters.dev/GoogleCloudPlatform/cloud-code-samples/python/django/python-hello-world](https://armadillo.dostuffthatmatters.dev/GoogleCloudPlatform/cloud-code-samples/python/django/python-hello-world)

<br/>

### Usage

You don't have to configure anything!

Just use/share (e.g. include in your `README`) a link in the following format:

```
https://armadillo.dostuffthatmatters.dev/{username}/{repository-name}{subdirectory-path}
```

**Armadillo** will return a `zip`-file of that subdirectory from the latest version of the default repository branch.

<br/>

### About the Implementation

Whenever a specific subdirectory of a repository is requested:

1. Checking the latest commit hash on the default branch
2. If a `zip`-file for that commit hash for this specific directory has not yet been generated, generate it now
3. Return that `zip`-file

_Note: The latest commit hash is always the one with respect to that subdirectory only. Meaning: When the subdirectory does not change with further commits the `zip`-file will not be regenerated as well._

<br/>
<br/>

_I am using this tool for a lecture I am holding. I have one repo for the whole semester with one subdirectory in it for every week._
_Students should not be required to download the whole repo every week and learning/using git is not a programming-introductory thing!_

[_buy me a coffee :)_](https://www.buymeacoffee.com/dstm)
