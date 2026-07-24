# Recursively process all .puml files and convert to .svg
Get-ChildItem -Path . -Recurse -Filter *.puml | ForEach-Object {
    $inputFile = $_.FullName
    $outputDir = $_.DirectoryName
    java -jar "C:\plantuml\plantuml.jar" -tsvg -o $outputDir $inputFile
}