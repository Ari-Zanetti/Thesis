package thesis;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.json.simple.JSONObject;
import org.json.simple.parser.ParseException;
import thesis.beans.SentencePair;

public class Main {

    private static final Map<String, Language[]> languages_map = new HashMap<String, Language[]>();

    static {
        languages_map.put("iten", new Language[]{Language.English, Language.Italian});
        languages_map.put("sven", new Language[]{Language.English, Language.Swedish});
        languages_map.put("svit", new Language[]{Language.Italian, Language.Swedish});
    }

    private static void run(String lang) {
        long time = System.currentTimeMillis();
        System.out.println("Loading sentences: " + lang);
        ServerUtilProcess bp = ServerUtilProcess.getInstanceBuild(lang);
        bp.run();
        time = System.currentTimeMillis() - time;
        System.out.println("Completed in: " + time);
    }

    public static void main(String[] args) throws IOException {
        String filename = "chosen_sentences";
        String outputfile = "output.txt";
        List<String> languages = Arrays.asList(new String[]{"iten", "sven", "svit"});
        File out = new File(outputfile);
        try (BufferedWriter bw = new BufferedWriter(new FileWriter(out))) {
            for (String lang : languages) {
                //Extracting new sentences
                //run(lang);

                //Calculating complexity
                bw.write(lang + "\n");
                Language[] langs = languages_map.get(lang);
                ReadabilityEstimator rest = ReadabilityEstimator.getInstance();
                File f = new File(filename + "_" + lang + ".txt");
                if (f.exists()) {
                    System.out.println("Reading sentences");
                    BufferedReader bf = new BufferedReader(new FileReader(f));
                    String line;
                    while ((line = bf.readLine()) != null) {
                        SentencePair sp = new SentencePair(line);
                        sp.getS1().setLanguage(langs[0]);
                        String chunks1 = bf.readLine();
                        sp.getS1().buildTokens(chunks1);

                        sp.getS2().setLanguage(langs[1]);
                        String chunks2 = bf.readLine();
                        sp.getS2().buildTokens(chunks2);

                        try {
                            rest.calculateReadability(sp.getS1());
                            rest.calculateReadability(sp.getS2());
                            bw.write(sp.getId() + ":" + sp.getS1().getComplexity() + " || " + sp.getS2().getComplexity() + "\n");
                        } catch (Exception ex) {
                            System.out.println("Error while calculating readability of the sentence");
                            bw.write(sp.getId()+": error");
                        }
                        /*System.out.println("Preparing JSON");
                        JSONObject json = sp.toJSON();
                        System.out.println(json.toJSONString());
                        bw.write(json.toJSONString());
                        bw.write("\n");*/
                    }
                } else {
                    System.out.println("File not found.");
                }
            }
            bw.close();
        }
    }
}
