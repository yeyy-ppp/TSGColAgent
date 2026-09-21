package humaneval.correct;

public class SUM_SQUARED_NUMS {
    public static long sum_squared_nums(double[] lst) {
        int result = 0;
        for(int i = 0; i < lst.length; i++) {
            result += (Math.ceil(lst[i])) * (Math.ceil(lst[i]));
        }
        return result;
    }
}
