plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

val syncSharedAssets = tasks.register<Copy>("syncSharedAssets") {
    from("../../imgs") {
        into("imgs")
    }
    from("../../fonts") {
        into("fonts")
    }
    into(layout.buildDirectory.dir("generated/sharedAssets"))
}

android {
    namespace = "com.frankmulvie.flowers"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.frankmulvie.flowers"
        minSdk = 24
        targetSdk = 34
        versionCode = 100
        versionName = "1.0.0"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }

    sourceSets {
        getByName("main") {
            assets.srcDir(layout.buildDirectory.dir("generated/sharedAssets"))
        }
    }
}

tasks.named("preBuild") {
    dependsOn(syncSharedAssets)
}
