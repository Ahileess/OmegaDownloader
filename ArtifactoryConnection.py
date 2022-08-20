from artifactory import ArtifactoryPath as AP

def Connection():
    path = AP(
        "https://artifactory.automiq.net/artifactory/automiq-build/automiq/Alpha.HMI.SetPoints/", 
        auth=("gorodilov_aa", "19031994Aleexx") 
        )
    return path.glob("**/*package*.tgz")




