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
  devtool: "eval-cheap-module-source-map", // Dev: fastest reasonable source maps
  // devtool: "source-map", // Dev: switch to full source maps for debugging if needed
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
        exclude: [
          /node_modules\/ecds-annotator/,
          /node_modules\/uikit/,
          /node_modules\/jquery/,
          /node_modules\/@selectize\/selectize/,
          /node_modules\/nouislider/,
        ],
      },
      {
        test: /\.css$/i,
        use: ["css-loader"],
      },
    ],
  },
};
