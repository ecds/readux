const path = require("path");
const webpack = require("webpack");
const BundleTracker = require("webpack-bundle-tracker");
const { VueLoaderPlugin } = require('vue-loader');

module.exports = {
  context: __dirname,
  mode: "production",
  entry: "./apps/static/js/index",
  watch: false,
  output: {
    path: path.resolve("./apps/static/js/"),
    filename: "[name].js",
  },
  resolve: {
    extensions: ['.js', '.vue', '.json'],
    alias: {
      // Use compiler+runtime build of Vue 2
      'vue$': 'vue/dist/vue.esm.js',
      '@': path.resolve(__dirname, 'apps/static/js'),
    },
  },
  devtool: "source-map",
  plugins: [new BundleTracker({ filename: "./webpack-stats.json" }), new VueLoaderPlugin()],
  module: {
    rules: [
      {
        test: /\.vue$/,
        loader: 'vue-loader',
      },
      {
        test: /\.js$/,
        enforce: "pre",
        use: ["source-map-loader"],
      },
      {
        test: /\.css$/i,
        use: ["css-loader"],
      },
    ],
  },
};
