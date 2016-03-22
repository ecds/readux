module.exports = function(grunt) {

  // Project configuration.
  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),

    copy: {
      main: {
        files: [
        { expand: true, cwd: './css', src: '*.css', dest: '../' },
        { expand: true, cwd: './css', src: '*.map', dest: '../' },

        ]
      }
    },

    sass: {
      build: {
        options: {
          style: 'expanded',
          precision: 8
        },
        files: {
          './css/annotator.css': './annotator.scss'
        }
      }
    },

    cssmin: {
      options: {
        shorthandCompacting: false,
        roundingPrecision: -1,
        sourceMap:true
      },
      target: {
        files: {
          './css/annotator.min.css': ['./css/annotator.css']
        }
      }
    },

    nodeunit: {
      all: ['test/*_tests.js']
    }
  });

  // load all grunt tasks
  grunt.loadNpmTasks('grunt-contrib-copy');
  grunt.loadNpmTasks('grunt-contrib-cssmin');
  grunt.loadNpmTasks('grunt-contrib-sass');


  //if you choose to use scss, or any preprocessor, you can add it here
  grunt.registerTask('default', ['sass', 'cssmin']);

  grunt.registerTask('replace', ['sass', 'cssmin', 'copy']);


  //travis CI task
  grunt.registerTask('travis', ['sass', 'cssmin', 'copy', 'nodeunit']);

};
