function getUniquesMenu(df, thisVariable) {

  var thisList = df.map(function(o) {
    return o[thisVariable]
  })

  // uniq() found here https://stackoverflow.com/questions/9229645/remove-duplicate-values-from-js-array
  function uniq(a) {
      return a.sort().filter(function(item, pos, ary) {
          return !pos || item != ary[pos - 1];
      });
  }

  var uniqueList = uniq(thisList);

  return uniqueList;
}

var capitalize = function(string) {
  return string.charAt(0).toUpperCase() + string.slice(1);
}

var nameNoSpaces = function(name) {
  let newName = name.toLowerCase().split(" ").join("")
      .replace("(", "")
      .replace(")", "")
      .replace(".", "")
      .replace("/", "");
  return newName;
}
