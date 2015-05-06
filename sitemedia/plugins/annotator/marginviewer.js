var clone,
  __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; },
  __hasProp = {}.hasOwnProperty;

clone = function(obj) {
  var key, newInstance;
  if ((obj == null) || typeof obj !== 'object') {
    return obj;
  }
  newInstance = new obj.constructor();
  for (key in obj) {
    newInstance[key] = clone(obj[key]);
  }
  return newInstance;
};

Annotator.Plugin.MarginViewerObjectStore = (function() {
  function MarginViewerObjectStore(data, paramFuncObject, _at_idfield, _at_marginobjfield, _at_indexfield) {
    var index, obj, _i, _ref;
    if (data == null) {
      data = [];
    }
    this.idfield = _at_idfield != null ? _at_idfield : "id";
    this.marginobjfield = _at_marginobjfield != null ? _at_marginobjfield : "_marginObject";
    this.indexfield = _at_indexfield != null ? _at_indexfield : "_marginindex";
    this.funcObject = clone(paramFuncObject);
    this.funcObject.sortDataComparison = (function(_this) {
      return function(x, y) {
        return paramFuncObject.sortComparison(x[0], y[0]);
      };
    })(this);
    this.funcObject.mapFunc = (function(_this) {
      return function(x) {
        return [paramFuncObject.sortDataMap(x), x];
      };
    })(this);
    this.data = data.map(this.funcObject.mapFunc);
    this.data.sort(this.funcObject.sortDataComparison);
    this.deletions = 0;
    this.insertions = 0;
    if (this.data.length!==undefined && this.data.length > 0) {
      for (index = _i = 0, _ref = this.data.length - 1; 0 <= _ref ? _i <= _ref : _i >= _ref; index = 0 <= _ref ? ++_i : --_i) {
        obj = this.data[index][1];
        obj[this.indexfield] = index;
      }
    }
  }

  MarginViewerObjectStore.prototype.getMarginObjects = function() {
    return this.data.map(function(x) {
      return x[1];
    });
  };

  MarginViewerObjectStore.prototype.updateObjectLocation = function(obj) {
    var objIndex;
    objIndex = this.getObjectLocation(obj);
    this.data[objIndex] = [this.funcObject.sortDataMap(obj), obj];
    return obj[this.indexfield] = objIndex;
  };

  MarginViewerObjectStore.prototype.objectEquals = function(obj1, obj2) {
    if (("id" in obj1) && ("id" in obj2)) {
      return obj1.id === obj2.id;
    }
    if (("id" in obj1) || ("id" in obj2)) {
      return false;
    }
    if ((this.indexfield in obj1) && (this.indexfield in obj2)) {
      return obj1[this.indexfield] === obj2[this.indexfield];
    }
    return false;
  };

  MarginViewerObjectStore.prototype.getObjectLocation = function(obj) {
    var currentObject, index, maximumIndex, minimumIndex, supposedLocation, _i;
    supposedLocation = obj[this.indexfield];
    if (this.data.length!==undefined && supposedLocation < this.data.length && this.objectEquals(this.data[supposedLocation][1], obj)) {
      return supposedLocation;
    }
    minimumIndex = Math.max(0, supposedLocation - this.deletions);
    maximumIndex = Math.min(this.data.length - 1, supposedLocation + this.insertions);
    for (index = _i = minimumIndex; minimumIndex <= maximumIndex ? _i <= maximumIndex : _i >= maximumIndex; index = minimumIndex <= maximumIndex ? ++_i : --_i) {
      currentObject = this.data[index][1];
      if (this.objectEquals(currentObject, obj)) {
        currentObject[this.indexField] = index;
        return index;
      }
    }
    return -1;
  };

  MarginViewerObjectStore.prototype.getNewLocationsForObject = function(top, bottom, obj) {
    var currentIndex, currentNewBottom, currentNewTop, currentObject, currentObjectBottom, currentObjectGoalBottom, currentObjectGoalLocation, currentObjectSize, currentObjectTop, locationChanges, objectIndex, objectNewTop;
    objectIndex = this.getObjectLocation(obj.annotation);
    currentIndex = objectIndex - 1;
    currentNewTop = top;
    currentNewBottom = bottom;
    locationChanges = [];
    while (currentIndex >= 0) {
      currentObject = this.data[currentIndex][1][this.marginobjfield];
      currentObjectSize = $(currentObject).outerHeight(true);
      currentObjectTop = $(currentObject).offset().top;
      currentObjectBottom = currentObjectTop + currentObjectSize;
      currentObjectGoalLocation = this.funcObject.sortDataMap(currentObject.annotation);
      currentObjectGoalBottom = currentObjectGoalLocation.top + currentObjectSize;
      if (currentObjectBottom > currentNewTop) {
        objectNewTop = currentNewTop - currentObjectSize;
        locationChanges.push([objectNewTop, currentObject]);
        currentNewTop = objectNewTop;
      } else {
        if (currentObjectGoalLocation.top > currentObjectTop) {
          if (currentObjectGoalBottom < currentNewTop) {
            objectNewTop = currentObjectGoalLocation.top;
            locationChanges.push([objectNewTop, currentObject]);
            currentNewTop = currentObjectGoalLocation.top;
          } else {
            objectNewTop = currentNewTop - currentObjectSize;
            locationChanges.push([objectNewTop, currentObject]);
            currentNewTop = objectNewTop;
          }
        } else {
          break;
        }
      }
      currentIndex -= 1;
    }
    currentIndex = objectIndex + 1;
    while (this.data.length!==undefined && currentIndex < this.data.length) {
      currentObject = this.data[currentIndex][1][this.marginobjfield];
      currentObjectSize = $(currentObject).outerHeight(true);
      currentObjectTop = $(currentObject).offset().top;
      currentObjectBottom = currentObjectTop + currentObjectSize;
      currentObjectGoalLocation = this.funcObject.sortDataMap(currentObject.annotation);
      currentObjectGoalBottom = currentObjectGoalLocation.top + currentObjectSize;
      if (currentObjectTop < currentNewBottom) {
        objectNewTop = currentNewBottom;
        locationChanges.push([objectNewTop, currentObject]);
        currentNewBottom = objectNewTop + currentObjectSize;
      } else {
        if (currentObjectGoalLocation.top < currentObjectTop) {
          if (currentObjectGoalLocation.top > currentNewBottom) {
            objectNewTop = currentObjectGoalLocation.top;
            locationChanges.push([objectNewTop, currentObject]);
            currentNewBottom = objectNewTop + currentObjectSize;
          } else {
            objectNewTop = currentNewBottom;
            locationChanges.push([objectNewTop, currentObject]);
            currentNewBottom = objectNewTop + currentObjectSize;
          }
        } else {
          break;
        }
      }
      currentIndex += 1;
    }
    return locationChanges;
  };

  MarginViewerObjectStore.prototype.findIndexForNewObject = function(location) {
    var currentIndex, endIndex, startIndex;
    startIndex = 0;
    endIndex = this.data.length;
    while (startIndex < endIndex) {
      currentIndex = Math.floor((startIndex + endIndex) / 2);
      if (this.funcObject.sortComparison(location, this.data[currentIndex][0]) > 0) {
        startIndex = currentIndex + 1;
      } else {
        endIndex = currentIndex;
      }
    }
    return startIndex;
  };

  MarginViewerObjectStore.prototype.addNewObject = function(obj, topval, leftval) {
    var location, newObjectLocation;
    location = {
      top: topval,
      left: leftval
    };
    newObjectLocation = this.findIndexForNewObject(location);
    this.data.splice(newObjectLocation, 0, this.funcObject.mapFunc(obj));
    obj[this.indexfield] = newObjectLocation;
    return this.insertions += 1;
  };

  MarginViewerObjectStore.prototype.deleteObject = function(object) {
    var objectLocation;
    objectLocation = this.getObjectLocation(object);
    this.data.splice(objectLocation, 1);
    return this.deletions += 1;
  };

  MarginViewerObjectStore.prototype.getObject = function(object) {
    var objectLocation;
    objectLocation = this.getObjectLocation(object);
    return this.data[objectLocation];
  };

  MarginViewerObjectStore.prototype.getNextObject = function(object) {
    var currentLocation;
    currentLocation = this.getObjectLocation(object);
    if (currentLocation + 1 < this.data.length) {
      return this.data[currentLocation + 1];
    } else {
      return null;
    }
  };

  return MarginViewerObjectStore;

})();

Annotator.Plugin.MarginViewer = (function(_super) {
  __extends(MarginViewer, _super);
  function MarginViewer(element, options) {
    MarginViewer.__super__.constructor.apply(this, arguments);
  }

  MarginViewer.prototype.events = {
    'annotationsLoaded': 'onAnnotationsLoaded',
    'annotationCreated': 'onAnnotationCreated',
    'annotationDeleted': 'onAnnotationDeleted',
    'beforeAnnotationUpdated': 'onBeforeAnnotationUpdated',
    'annotationUpdated': 'onAnnotationUpdated',
    '.annotator-hl click': 'onAnnotationSelected'
  };

  MarginViewer.prototype.pluginInit = function() {
    var RTL_MULT, sign;
    if (!Annotator.supported()) {
      return;
    }

    this.annotator.viewer = {
      on: function() {},
      hide: (function(_this) {
        return function(annotations) {
          return _this.hideHighlightedMargin(annotations);
        };
      })(this),
      load: (function(_this) {
        return function(annotations) {
          return _this.highlightMargin(annotations);
        };
      })(this),
      isShown: function() {},
      addField: function() {},
      element: {
        position: function() {},
        css: function() {}
      }
    };
    this.highlightedObjects = [];
    this.currentSelectedAnnotation = null;
    RTL_MULT = -1;
    sign = function(x) {
      if (x === 0) {
        return 0;
      } else {
        return x / Math.abs(x);
      }
    };
    this.funcObject = {
      sortDataMap: function(annotation) {
        var dbg;
        if (annotation.highlights){
          dbg = {
            top: $(annotation.highlights[0]).offset().top,
            left: $(annotation.highlights[0]).offset().left
          };
        }
        return dbg;
      },
      sortComparison: function(left, right) {
        return sign(sign(left.top - right.top) * 2 + sign(left.left - right.left) * RTL_MULT);
      },
      idFunction: function(annotation) {
        return annotation.id;
      },
      sizeFunction: function(element) {
        return element.outerHeight(true);
      }
    };

    this.store = undefined;

    var self = this;
    $("#toggle-annotations").on('click',function(evt){
      evt.preventDefault();
      var $secondary = $(".secondary");

      if($secondary.css('right')=="0px"){
          self.showAnnotations();
      }
      else{
        self.hideAnnotations();
      }
    });


    return this.marginData = new Annotator.Plugin.MarginViewerObjectStore([], this.funcObject);
  };

  MarginViewer.prototype.showAnnotations = function(){
    var width = $(".secondary").width()/2,
        offset = (-1*width) - 15;

    $(".annotator-wrapper").animate({left: offset },500);
    $(".secondary").animate({opacity:1,right: offset });
    $(".carousel-control").fadeOut();

    var $toggle = $("#toggle-annotations");
    $toggle.animate({right:"135px"},500);
    $toggle.find("span").attr("class","fa fa-arrow-left");

  };

  MarginViewer.prototype.hideAnnotations = function(){
    $(".annotator-wrapper").animate({left:"0"},500);
    $(".secondary").animate({opacity:0,right:"0"});
    $(".carousel-control").fadeIn();
    $(".annotator-hl-uber").attr({class:"annotator-hl"});

    var $toggle = $("#toggle-annotations");
    $toggle.animate({right:"-15px"},500);
    $toggle.find("span").attr("class","fa fa-file-text-o");
  };

  MarginViewer.prototype.onAnnotationsLoaded = function(annotations) {
    var annotation, annotationStart, currentLocation, marginObject, newLocation, _i, _len, _ref, _results;
    this.marginData = new Annotator.Plugin.MarginViewerObjectStore(annotations, this.funcObject);
    if (annotations.length > 0) {
      currentLocation = 0;
      _ref = this.marginData.getMarginObjects();
      _results = [];
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        annotation = _ref[_i];
        annotationStart = annotation.highlights[0];
        newLocation = $(annotationStart).offset().top;
        if (currentLocation > newLocation) {
          newLocation = currentLocation;
        }
        marginObject = this.createMarginObject(annotation, newLocation);
        this.marginData.updateObjectLocation(annotation);
        _results.push(currentLocation = $(marginObject).offset().top + $(marginObject).outerHeight(true));
      }
      return _results;
    }
  };

  MarginViewer.prototype.onAnnotationCreated = function(annotation) {
    var hide, marginObject, newObjectBottom, newObjectTop;
    marginObject = this.createMarginObject(annotation, hide = true);
    newObjectTop = $(annotation.highlights[0]).offset().top;
    newObjectBottom = newObjectTop + $(marginObject).outerHeight(true);
    this.marginData.addNewObject(annotation, newObjectTop, $(annotation.highlights[0]).offset().left);
    $(marginObject).fadeIn('fast');
    return this.onMarginSelected(marginObject);
  };

  MarginViewer.prototype.onAnnotationSelected = function(event) {
    var annotations, i, selectIndex, _i, _ref;
    event.stopPropagation();
    annotations = $(event.target).parents('.annotator-hl').andSelf().map(function() {
      return $(this).data("annotation");
    });
    selectIndex = 0;
    if (annotations.length > 1) {
      for (i = _i = 0, _ref = annotations.length - 1; 0 <= _ref ? _i <= _ref : _i >= _ref; i = 0 <= _ref ? ++_i : --_i) {
        if ($(annotations[i]._marginObject).hasClass("annotator-marginviewer-selected")) {
          selectIndex = (i + 1) % annotations.length;
          break;
        }
      }
    }
    return this.onMarginSelected(annotations[selectIndex]._marginObject);
  };

  MarginViewer.prototype.onAnnotationDeleted = function(annotation) {
    var nextObject;
    nextObject = this.marginData.getNextObject(annotation);
    this.marginData.deleteObject(annotation);
    if (nextObject !== null) {
      return this.onMarginSelected(nextObject[1]._marginObject);
    }
  };

  MarginViewer.prototype.zeroPad = function(num, count) {
    var numZeroPad;
    numZeroPad = String(num);
    while (numZeroPad.length < count) {
      numZeroPad = "0" + numZeroPad;
    }
    return numZeroPad;
  };

  MarginViewer.prototype.formattedDateTime = function(dateobj) {
    var dateString, meridiemString, timeString;
    meridiemString = dateobj.getHours() < 12 ? "AM" : "PM";
    timeString = dateobj.getHours() + ":" + this.zeroPad(dateobj.getMinutes(), 2) + meridiemString;
    dateString = this.zeroPad(dateobj.getDate(), 2) + "." + this.zeroPad(dateobj.getMonth(), 2) + "." + dateobj.getFullYear();
    return timeString + " " + dateString;
  };

  MarginViewer.prototype.renderMarginObject = function(annotation) {
    var datetime, delel, user;
    datetime = annotation.created ? this.formattedDateTime(new Date(annotation.created)) : '';
    // user = this.annotator.plugins.AnnotateItPermissions.user.userId;
    // delel = annotation.user === user || annotation.permissions["delete"].indexOf(user) >= 0 ? '<span class="annotator-marginviewer-delete" style="float: left; direction: ltr;">X</span>' : '';
    controls = '<span class="annotator-controls"><button class="annotator-edit">Edit</button><button class="annotator-delete">Delete</button></span>';
    id = annotation.id;
    text = Markdown(annotation.text);
    return '<div class="annotator-marginviewer-element"><div class="annotator-marginviewer-header"><span class="annotator-marginviewer-user">' + annotation.user + '</span> | <span class="annotator-marginviewer-date" style="direction: ltr;">' + datetime + '</span></div>'+ controls +'<div class="annotator-marginviewer-text" id="'+id+'">' + text + '</div></div>';
  };

  MarginViewer.prototype.createMarginObject = function(annotation, location, hide) {
    var marginObject, marginObjects;
    if (location == null) {
      location = null;
    }
    if (hide == null) {
      hide = false;
    }
    marginObjects = $(this.renderMarginObject(annotation)).appendTo('.secondary').click((function(_this) {
      return function(event) {
        return _this.onMarginSelected(event.target);
      };
    })(this)).mouseenter((function(_this) {
      return function(event) {
        return _this.onMarginMouseIn(event.target);
      };
    })(this)).mouseleave((function(_this) {
      return function(event) {
        return _this.onMarginMouseOut(event.target);
      };
    })(this));
    marginObjects.children(".annotator-controls").children(".annotator-edit").click((function(_this) {
      return function(event) {
        var $parent = $(this).parent('.annotator-controls'),
            $text_container = $parent.siblings(".annotator-marginviewer-text");

        if($text_container.attr('id')=="undefined"){
          $text_container.attr('id',annotation.id);
          var $header = $parent.siblings(".annotator-marginviewer-header");
          $header.find(".annotator-marginviewer-user").html(annotation.user);
          $header.find(".annotator-marginviewer-date").html(_this.formattedDateTime(new Date(annotation.created)));
        }
        return _this.onMarginEdit(event.target);
      };
    })(this));
    marginObjects.children(".annotator-controls").children(".annotator-delete").click((function(_this) {
      return function(event) {
        return _this.onMarginDeleted(event.target);
      };
    })(this));
    if (location !== null) {
      marginObjects.offset({
        top: location
      });
    }
    if (hide) {
      marginObjects.hide();
    }

    marginObject = marginObjects[0];
    annotation._marginObject = marginObject;
    marginObject.annotation = annotation;//jQuery.extend(true, {},annotation);
    return marginObject;
  };

  MarginViewer.prototype.onBeforeAnnotationUpdated = function(annotation) {
    // Due to how the margins are being related to the annotation,
    // we need to remove the _marginObject attribute before saving
    // the annotation.

    // First, store the circular reference _marginObject
    this.store = annotation._marginObject;
    // Then delete the circular object.
    delete annotation._marginObject;
    return annotation;
  };

  MarginViewer.prototype.onAnnotationUpdated = function(annotation) {
    // Update the margin annotation text
    var id = "#"+ annotation.id,
        text = Markdown(annotation.text);

    $(id).html(text);

    // Restore the _marginObject attribute to the annotation object.
    annotation._marginObject = this.store;
    // Then clear the store variable.
    this.store = undefined;

    // Hide the viwer and select the annotation in the margin.
    $(".annotator-editor").not(".annotator-hide").addClass("annotator-hide");
    this.onMarginSelected(annotation._marginObject);
    return annotation;
  };

  MarginViewer.prototype.onMarginMouseIn = function(obj) {
    var $margin_annotation = $(obj).closest(".annotator-marginviewer-element")[0];
    return $($margin_annotation.annotation.highlights).addClass("annotator-hl-uber-temp").removeClass("annotator-hl");
  };

  MarginViewer.prototype.onMarginMouseOut = function(obj) {
    var $margin_annotation = $(obj).closest(".annotator-marginviewer-element")[0];
    return $($margin_annotation.annotation.highlights).addClass("annotator-hl").removeClass("annotator-hl-uber-temp");
  };

  MarginViewer.prototype.onMarginSelected = function(obj) {
    var annotation, currentMarginObject, currentObjectNewTop, horizontalSlide, marginObject, newBottom, newLocationsByObject, newTop;
    marginObject = $(obj).closest(".annotator-marginviewer-element")[0];
    annotation = marginObject.annotation;
    horizontalSlide = [];
    newTop = $(annotation.highlights[0]).offset().top;
    newBottom = $(marginObject).outerHeight(true) + newTop;
    newLocationsByObject = this.marginData.getNewLocationsForObject(newTop, newBottom, marginObject);

    this.showAnnotations();

    if (this.currentSelectedAnnotation !== null) {
      if (annotation.id === this.currentSelectedAnnotation.id) {
        return;
      } else {
        currentMarginObject = this.currentSelectedAnnotation._marginObject;
        if (currentMarginObject !== null) {
          $(this.currentSelectedAnnotation.highlights).removeClass("annotator-hl-uber").removeClass("annotator-hl-uber-temp").addClass("annotator-hl");
          currentObjectNewTop = $(currentMarginObject).offset().top;
          newLocationsByObject = $.grep(newLocationsByObject, function(value) {
            if (value[1].annotation.id === currentMarginObject.annotation.id) {
              currentObjectNewTop = value[0];
              return false;
            } else {
              return true;
            }
          });
          horizontalSlide.push([currentObjectNewTop, "+=20px", currentMarginObject]);
          $(currentMarginObject).removeClass("annotator-marginviewer-selected");
        }
      }
    }
    $(marginObject).addClass("annotator-marginviewer-selected");
    horizontalSlide.push([newTop, "-=20px", marginObject]);
    this.moveObjectsToNewLocation(newLocationsByObject, horizontalSlide);
    $(annotation.highlights).addClass("annotator-hl-uber").removeClass("annotator-hl");
    return this.currentSelectedAnnotation = annotation;
  };

  MarginViewer.prototype.onMarginEdit = function(obj) {
    var annotation, marginObject;
    marginObject = $(obj).closest(".annotator-marginviewer-element")[0];
    annotation = marginObject.annotation;
    position=$(annotation.highlights[0]).offset();
    position.top = position.top - 280;
    position.left = position.left - 200;
    return this.annotator.showEditor(annotation,position);
  };

  MarginViewer.prototype.onMarginDeleted = function(obj) {
    var annotation, marginObject;
    marginObject = $(obj).closest(".annotator-marginviewer-element")[0];
    annotation = marginObject.annotation;
    $(marginObject).remove();
    annotation._marginObject = null;
    return this.annotator.deleteAnnotation(annotation);
  };

  MarginViewer.prototype.moveObjectsToNewLocation = function(newLocations, horizontalSlideObjects) {
    var currentObject, horizontalSlide, newLocationStructure, newMarginRight, newTop, _i, _j, _len, _len1, _results;
    if (horizontalSlideObjects == null) {
      horizontalSlideObjects = [];
    }
    for (_i = 0, _len = newLocations.length; _i < _len; _i++) {
      newLocationStructure = newLocations[_i];
      newTop = newLocationStructure[0];
      currentObject = newLocationStructure[1];
      $(currentObject).animate({
        top: "+=" + (newTop - $(currentObject).offset().top)
      }, 'fast', 'swing');
      this.marginData.updateObjectLocation(currentObject.annotation);
    }
    _results = [];
    for (_j = 0, _len1 = horizontalSlideObjects.length; _j < _len1; _j++) {
      horizontalSlide = horizontalSlideObjects[_j];
      newTop = horizontalSlide[0];
      newMarginRight = horizontalSlide[1];
      currentObject = horizontalSlide[2];
      $(currentObject).animate({
        top: "+=" + (newTop - $(currentObject).offset().top)
      }, 'fast', 'swing');
      _results.push(this.marginData.updateObjectLocation(currentObject.annotation));
    }
    return _results;
  };

  MarginViewer.prototype.highlightMargin = function(annotations) {
    var existingHighlight, found, marginObjects, newHighlight, oldObjects, _i, _j, _len, _len1, _ref;
    if (this.highlightedObjects.length > 0) {
      oldObjects = [];
      _ref = this.highlightedObjects;
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        existingHighlight = _ref[_i];
        found = false;
        for (_j = 0, _len1 = annotations.length; _j < _len1; _j++) {
          newHighlight = annotations[_j];
          if (newHighlight.id === existingHighlight.id) {
            found = true;
          }
        }
        if (!found) {
          oldObjects.push(existingHighlight);
        }
      }
      this.hideHighlightedMargin(oldObjects);
    }
    this.highlightedObjects = annotations;
    marginObjects = jQuery.map(annotations, function(val, i) {
      return val._marginObject;
    });
    return $(marginObjects).addClass("annotator-marginviewer-highlighted");
  };

  MarginViewer.prototype.hideHighlightedMargin = function(annotations) {
    var marginObjects;
    this.highlightedObjects = [];
    marginObjects = jQuery.map(annotations, function(val, i) {
      return val._marginObject;
    });
    return $(marginObjects).removeClass("annotator-marginviewer-highlighted");
  };

  return MarginViewer;

})(Annotator.Plugin);

// ---
// generated by coffee-script 1.9.0
