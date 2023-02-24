class Popup {
    constructor(div, padding) {
      const vis = this;
  
      vis.div = div;
      vis.padding = padding || 20;
  
      vis.div.attr("class", "ei-popup")
          .style("display", "none");
    }
  
  
    update(text, left, top) {
      const vis = this;
  
      vis.div.style("display", "block")
        .html(text);

      const popupRect = vis.div.node().getBoundingClientRect();
  
      vis.div.style("top", `${top - popupRect.height - vis.padding}px`)
        .style("left", `${left - popupRect.width / 2 + vis.padding}px`);
    }
  
    hide() {
      const vis = this;
  
      vis.div.style("display", "none");
    }
  }
  