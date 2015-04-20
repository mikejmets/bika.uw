"use strict";

// Duplicate handlers between widgets; older jqueries
function bind_handlers1(src_selector, target_selector) {
	// iterate event types of original
	$.each($(src_selector).data('events'), function () {
		// iterate registered handler of original
		$.each(this, function () {
			$(target_selector).bind(this.type, this.handler);
		});
	});
}

// Duplicate handlers between widgets; newer jqueries
function bind_handlers2(src_selector, target_selector) {
	$.each($._data($(src_selector).get(0), 'events'), function () {
		// iterate registered handler of original
		$.each(this, function () {
			$(target_selector).bind(this.type, this.handler);
		});
	});
}

jQuery(function ($) {
	$(document).ready(function () {
		// Duplicate widgets render elements with identical attributes; rename them:
		$.each($("span.uw-dup div.field"), function (i, e) {
			var fieldname = $(e).attr("data-fieldname")
			// rename the widget div
			$(e).attr("data-fieldname", fieldname + "_dup")
			$(e).attr("id", "archetypes-widget-" + fieldname + "_dup")
			$.each($(e).find("input"), function (ii, ee) {
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
