
import org.gradle.api.DefaultTask
import org.gradle.api.tasks.TaskAction

class CopyToLib extends DefaultTask {

    CopyToLib() {
        dependsOn("jar")
    }

    @TaskAction
    def run() {
        def libDir = project.file('build/output/lib')
        libDir.mkdirs()
        project.configurations.default.each { File file -> 
            ant.copy(file: file.path, toDir: libDir) 
        }
        project.configurations.default.allArtifacts.each { artifact -> 
            ant.copy(file: artifact.file, todir: libDir) 
        }
    }

}
