package humaneval.correct;

public class EAT {
    public static int[] eat(int number, int need, int remaining) {
        if (need <= remaining) {
            return new int[] {number + need,  remaining - need};
        }
        else {
            return new int[] {number + remaining , 0};
        }
    }
}
