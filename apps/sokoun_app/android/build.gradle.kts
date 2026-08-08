allprojects {
    repositories {
        google()
        mavenCentral()
    }
}

val newBuildDir: Directory =
    rootProject.layout.buildDirectory
        .dir("../../build")
        .get()
rootProject.layout.buildDirectory.value(newBuildDir)

subprojects {
    val newSubprojectBuildDir: Directory = newBuildDir.dir(project.name)
    project.layout.buildDirectory.value(newSubprojectBuildDir)
}
subprojects {
    project.evaluationDependsOn(":app")
}

// Keep Java/Kotlin JVM targets consistent across Android library (plugin) subprojects.
// Plugins that don't declare jvmTarget (e.g. flutter_facebook_auth) get KGP's default
// (the Gradle JDK, 17) while javac may default to 1.8, which fails KGP's JVM-target
// validation. Align each plugin's Kotlin target with its own effective Java target.
// The :app module keeps its own explicit Java 11 config.
gradle.projectsEvaluated {
    rootProject.subprojects {
        if (plugins.hasPlugin("com.android.library")) {
            val javaTarget = extensions
                .findByType(com.android.build.gradle.BaseExtension::class.java)
                ?.compileOptions?.targetCompatibility?.toString()
                ?: JavaVersion.VERSION_1_8.toString()
            tasks.withType<org.jetbrains.kotlin.gradle.tasks.KotlinCompile>().configureEach {
                kotlinOptions.jvmTarget = javaTarget
            }
        }
    }
}

tasks.register<Delete>("clean") {
    delete(rootProject.layout.buildDirectory)
}
