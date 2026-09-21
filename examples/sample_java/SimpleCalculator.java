package sample;

public final class SimpleCalculator {
    public int add(int left, int right) {
        return left + right;
    }

    public int clamp(int value, int minimum, int maximum) {
        if (minimum > maximum) {
            throw new IllegalArgumentException("minimum must not exceed maximum");
        }
        if (value < minimum) {
            return minimum;
        }
        if (value > maximum) {
            return maximum;
        }
        return value;
    }

    public int divide(int dividend, int divisor) {
        if (divisor == 0) {
            throw new ArithmeticException("division by zero");
        }
        return dividend / divisor;
    }
}
