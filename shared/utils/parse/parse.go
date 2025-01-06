package parse

import (
	"math"
	"strconv"
)

// Round rounds the given number to the specified precision (number of decimal
// places).
//
// The number is first scaled up by 10 to the power of the precision, rounded
// to the nearest integer, and then scaled back down by the same factor.
func Round(number float64, precision int) float64 {
	scale := math.Pow10(precision)
	return math.Round(number*scale) / scale
}

// ToFloat parses the given string as a float64 and rounds it to the specified
// precision (number of decimal places).
//
// If the string cannot be parsed as a float64, an error is returned.
func ToFloat(number string, precision int) (float64, error) {
	parsed, err := strconv.ParseFloat(number, 64)
	if err != nil {
		return 0, err
	}

	return Round(parsed, precision), nil
}
