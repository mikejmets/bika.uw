"use strict";

jQuery(function ($) {
	$(document).ready(function () {

		// Duplicate widgets render elements with identical attributes; rename them:
		$.each($("span.uw-dup div.field"), function (i, e) {
			var fieldname = $(e).attr("data-fieldname")
			// rename the widget div
			$(e).attr("data-fieldname", fieldname + "_dup")
			$(e).attr("id", "archetypes-widget-" + fieldname + "_dup")

			//INPUT and TEXTAREA have almost-identical code
			$.each($(e).find("input").not(":hidden"), function (ii, ee) {
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


			//INPUT and TEXTAREA have almost-identical code
			$.each($(e).find("textarea"), function (ii, ee) {
				// rename individual textarea elements
				$(ee).attr("id", $(ee).attr("id").replace(fieldname, fieldname + "_dup"))
				$(ee).attr("name", $(ee).attr("name").replace(fieldname, fieldname + "_dup"))
			})
			// synchronise original with dups
			$("textarea#" + fieldname).bind("change", function () { $("textarea#" + fieldname + "_dup").val($(this).val()) })
			$("textarea#" + fieldname + "_uid").bind("change", function () { $("textarea#" + fieldname + "_dup_uid").val($(this).val()) })
			// synchronise dups with original
			$("textarea#" + fieldname + "_dup").bind("change", function () { $("textarea#" + fieldname).val($(this).val()) })
			$("textarea#" + fieldname + "_dup_uid").bind("change", function () { $("textarea#" + fieldname + "_uid").val($(this).val()) })

		})
	})
})
