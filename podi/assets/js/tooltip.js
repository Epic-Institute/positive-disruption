class Tooltip {
  constructor(div, padding) {
    const vis = this;

    vis.div = div;
    vis.padding = padding || 20;

    vis.div.attr("class", "ei-tooltip")
        .style("display", "none");
  }

  // updateText(text) {
  //   const vis = this;

  //   vis.div.html(text);
  // }

  update(text, left, top, orient = 'top') {
    const vis = this;

    vis.div.style("display", "block")
      .html(text);

    const tooltipRect = vis.div.node().getBoundingClientRect();
    let leftShift;
    if (left + tooltipRect.width + vis.padding > window.innerWidth) {
      if (orient === 'top') {
        leftShift = -(left + tooltipRect.width - window.innerWidth - vis.padding);
      } else {
        leftShift = -tooltipRect.width  - vis.padding;
      }
    } else {
      leftShift = 0;
    }
    const topShift = top + tooltipRect.height > window.innerHeight ? -(top + tooltipRect.height - window.innerHeight) : 0;
    const leftOffset = orient === 'top' ? -tooltipRect.width/2  + vis.padding : vis.padding;
    const topOffset = orient === 'top' ? -tooltipRect.height - vis.padding : 0;

    vis.div.style("top", `${top + topOffset + topShift}px`)
      .style("left", `${left + leftOffset + leftShift}px`);
  }

  hide() {
    const vis = this;

    vis.div.style("display", "none");
  }
}
