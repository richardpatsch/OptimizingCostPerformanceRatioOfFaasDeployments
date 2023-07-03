# install dependencies:
mvn dependency:copy-dependencies

# build jar
mvn package

# deploy
upload jar file (target/ir_java17......jar)


# set java home for maven:
export JAVA_HOME=/usr/local/Cellar/openjdk@17/17.0.7/libexec/openjdk.jdk/Contents/Home 
