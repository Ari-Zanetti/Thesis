package thesis;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;


public class ServerUtilProcess implements Runnable {
    
    private final List<String> parameters;
    
    private ServerUtilProcess(List<String> parameters){
        this.parameters = parameters;
    }
    
    public static ServerUtilProcess getInstanceBuild(String lang) {
        return new ServerUtilProcess(Arrays.asList(new String[]{"-M 0", "-l " + lang}));
    }

    @Override
    public void run() {
        try {
            List<String> commandList = new ArrayList(Arrays.asList(new String[]{"python3", "src/thesis/utils/word_alignment_corpus_builder.py"}));
            for(String s: parameters) {
                commandList.add(s);
            }
            Process p = new ProcessBuilder(commandList).start();
            BufferedReader reader = new BufferedReader(new InputStreamReader(p.getInputStream()));
            BufferedReader errReader = new BufferedReader(new InputStreamReader(p.getErrorStream()));
            StringBuilder builder = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) {
                builder.append(line);
                builder.append(System.getProperty("line.separator"));
            }

            String result = builder.toString().trim();

            StringBuilder errors = new StringBuilder();
            while ((line = errReader.readLine()) != null) {
                errors.append(line);
                errors.append(System.getProperty("line.separator"));
            }
            p.waitFor();
            System.out.println("Written file: " + result);
            System.out.println("Received errors: " + errors);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

}
