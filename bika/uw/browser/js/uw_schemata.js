"use strict";

jQuery(function ($) {
	$(document).ready(function () {
		// Duplicate widgets render elements with identical attributes; rename them:
		$.each($("span.uw-dup div.field"), function (i, e) {
			var fieldname = $(e).attr("data-fieldname")
			// rename the widget div
			$(e).attr("data-fieldname", fieldname + "_dup")
			$(e).attr("id", "archetypes-widget-" + fieldname + "_dup")
			$.each($(e).find("input[type='text'], input[id$='_uid']"), function (ii, ee) {
				// rename individual input elements
				$(ee).attr("id", $(ee).attr("id").replace(fieldname, fieldname + "_dup"))
				$(ee).attr("name", $(ee).attr("name").replace(fieldname, fieldname + "_dup"))
			})
			// synchronise original with dups
			$("input#" + fieldname).bind("selected change", function () { $("input#" + fieldname + "_dup").val($(this).val()) })
			$("input#" + fieldname + "_uid").bind("change", function () { $("input#" + fieldname + "_dup_uid").val($(this).val()) })
			// synchronise dups with original
			$("input#" + fieldname + "_dup").bind("selected change", function () { $("input#" + fieldname).val($(this).val()) })
			$("input#" + fieldname + "_dup_uid").bind("change", function () { $("input#" + fieldname + "_uid").val($(this).val()) })
		})
	})
})
