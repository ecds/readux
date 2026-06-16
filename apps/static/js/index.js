import $ from 'jquery'
import axios from 'axios'
import noUiSlider from 'nouislider'
import '@selectize/selectize'
import UIkit from 'uikit'
import UIkitIcons from 'uikit/dist/js/uikit-icons'
import ECDSAnnotator from 'ecds-annotator/dist/ecds-annotator.min.js'
import './vue-readux.js'

// Expose globals for non-module scripts (search.js, project.js, etc.)
window.$ = $
window.jQuery = $
window.axios = axios
window.noUiSlider = noUiSlider
UIkit.use(UIkitIcons)
window.UIkit = UIkit
window.UIkitIcons = UIkitIcons
window.ECDSAnnotator = ECDSAnnotator
