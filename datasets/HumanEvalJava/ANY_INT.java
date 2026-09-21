package humaneval.correct;

public class ANY_INT {
    public static boolean any_int(double x, double y, double z) {
        if ((int)x == x && (int)y == y && (int)z == z) {
            if (x + y == z || x + z == y || y + z == x)
                return true;
        }
        return false;
    }
}
