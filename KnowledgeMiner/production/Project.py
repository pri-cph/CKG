import project_config as config
import datasets_cypher as cypher
from KnowledgeConnector import graph_controller
import KnowledgeViewer.analyses.basicAnalysis as analyses
from KnowledgeViewer.plots import basicFigures as figure
import itertools

class Project:
    def __init__(self,identifier, project_type, datasets = [], report = {}):
        self.identifier = identifier
        self.project_type = project_type
        self.datasets = datasets
        self.report = {}
        if len(datasets) == 0:
            self.buildProject()
            self.generateReport()

    def getIdentifier(self):
        return self.identifier

    def getProject_type(self):
        return self.project_type

    def getDatasets(self):
        return self.datasets

    def getReport(self):
        return self.report

    def setIdentifier(self, identifier):
        self.identifier = identifier

    def setProject_type(self, project_type):
        self.project_type = project_type

    def setDatasets(self, datasets):
        self.datasets = datasets

    def setReport(self, report):
        self.report = report

    def addDataset(self, dataset):
        self.datasets.append(dataset)

    def updateReport(self, new):
        self.report.update(new)

    def buildProject(self):
        for dataset_type in config.configuration:
            if dataset_type == "proteomics":
                proteomicsDataset = ProteomicsDataset(self.getIdentifier(), config.configuration[dataset_type])
                self.addDataset(proteomicsDataset)

                
    def generateReport(self):
        for dataset in self.getDatasets():
                report = dataset.generateReport()
                self.updateReport({dataset.getType():report})
    
    def showReport(self):
        for dataset_type in self.getReport():
            print(dataset_type)
            print(self.getReport()[dataset_type].getPlots())

class Report:
    def __init__(self,identifier, plots = []):
        self.identifier = identifier
        self.plots = plots

    def getIdenfitifer(self):
        return self.identifier

    def getPlots(self):
        return self.plots

    def setIdentifier(self, identifier):
        self.identifier = identifier

    def setPlots(self, plots):
        self.plots = plots

    def addPlot(self, plot):
        self.plots.append(plot)

    def extendPlots(self, plots):
        self.plots.extend(plots)

class AnalysisResult:
    def __init__(self, identifier, analysis_type, args, data, result = None):
        self.identifier = identifier
        self.analysis_type = analysis_type
        self.args = args
        self.data = data
        self.result = result
        if self.result is None:
            self.generateResult()

    def getIdentifier(self):
        return self.identifier

    def getAnalysisType(self):
        return self.analysis_type

    def getArguments(self):
        return self.args

    def getData(self):
        return self.data

    def getResult(self):
        return self.result

    def setIdentifier(self, identifier):
        self.identifier = identifier

    def setAnalysisType(self, analysis_type):
        self.analysis_type = analysis_type

    def setArguments(self, args):
        self.args = args

    def setData(self, data):
        self.data = data

    def setResult(self, result):
        self.result = result

    def generateResult(self):
        result, args = self.getAnalysisResult()
        self.setResult(result)
        self.setArguments(args)

    def getAnalysisResult(self):
        result = {}
        args = self.getArguments()
        if self.getAnalysisType() == "pca":
            components = 2
            if "components" in args:
                components = args["components"]
            result, args = analyses.runPCA(self.getData(), components)
        elif self.getAnalysisType()  == "tsne":
            components = 2
            perplexity = 40
            n_iter = 1000
            init='pca'
            if "components" in args:
                components = args["components"]
            if "perplexity" in args:
                perplexity = args["perplexity"]
            if "n_iter" in args:
                n_iter = args["n_iter"]
            if "init" in args:
                init = args["init"]
            result, args = analyses.runTSNE(self.getData(), components=components, perplexity=perplexity, n_iter=n_iter, init=init)
        elif self.getAnalysisType()  == "umap":
            n_neighbors=10 
            min_dist=0.3
            metric='cosine'
            if "n_neighbors" in args:
                n_neighbors = args["n_neighbors"]
            if "min_dist" in args:
                min_dist = args["min_dist"]
            if "metric" in args:
                metric = args["metric"]
            if n_neighbors < self.getData().shape[0]:
                result, args = analyses.runUMAP(self.getData(), n_neighbors=n_neighbors, min_dist=min_dist, metric=metric)
        elif self.getAnalysisType()  == 'ttest':
            alpha = 0.05
            if "alpha" in args:
                alpha = args["alpha"]
            for pair in itertools.combinations(self.getData().group.unique(),2):
                ttest_result = analyses.ttest(self.getData(), pair[0], pair[1], alpha = 0.05)
                result[pair] = ttest_result
        elif self.getAnalysisType()  == 'anova':
            alpha = 0.05
            if "alpha" in args:
                alpha = args["alpha"]
            anova_result = analyses.anova(self.getData(), alpha = 0.05)
            result = anova_result
        elif self.getAnalysisType()  == "correlation":
            alpha = 0.05
            method = 'pearson'
            correction = ('fdr', 'indep')
            if "alpha" in args:
                alpha = args["args"]
            if "method" in args:
                method = args["method"]
            if "correction" in args:
                correction = args["correction"]
            result[self.getAnalysisType()] = analyses.runCorrelation(self.getData(), alpha=alpha, method=method, correction=correction)
         
        return result, args

    def getPlot(self, name, identifier, title):
        data = self.getResult()
        args = self.args
        plot = [] 
        if name == "basicTable":
            colors = ('#C2D4FF','#F5F8FF')
            attr =  {'width':800, 'height':300, 'font':12}
            subset = None
            if "colors" in args:
                colors = args["colors"]
            if "attr" in args:
                attr = args["attr"]
            if "subset" in args:
                subset = args["subset"]
            for id in data:
                if isinstance(id, tuple):
                    identifier = identifier+"_"+id[0]+"_vs_"+id[1]
                    figure_title = title + id[0]+" vs "+id[1]
                else:
                    figure_title = title
                plot.append(figure.getBasicTable(data[id], identifier, figure_title, colors=colors, subset=subset, plot_attr=attr))
        elif name == "basicBarPlot":
            x_title = "x"
            y_title = "y"
            if "x_title" in args:
                x_title = args["x_title"]
            if "y_title" in args:
                y_title = args["y_title"]
            for id in data:     
                if isinstance(id, tuple):
                    identifier = identifier+"_"+id[0]+"_vs_"+id[1]
                    figure_title = title + id[0]+" vs "+id[1]
                else:
                    figure_title = title
                plot.append(figure.getBarPlotFigure(data[id], identifier, figure_title, x_title, y_title))
        elif name == "scatterPlot":
            x_title = "x"
            y_title = "y"
            if "x_title" in args:
                x_title = args["x_title"]
            if "y_title" in args:
                y_title = args["y_title"]
            for id in data:
                if isinstance(id, tuple):
                    identifier = identifier+"_"+id[0]+"_vs_"+id[1]
                    figure_title = title + id[0]+" vs "+id[1]
                else:
                    figure_title = title
                plot.append(figure.getScatterPlotFigure(data[id], identifier, figure_title, x_title, y_title))
        elif name == "volcanoPlot":
            alpha = 0.05
            lfc = 1.0
            if "alpha" in args:
                alpha = args["alpha"]
            if "lfc" in args:
                lfc = args["lfc"]
            for pair in data:
                signature = data[pair]
                p = figure.runVolcano(identifier+"_"+pair[0]+"_vs_"+pair[1], signature, lfc=lfc, alpha=alpha, title=title+" "+pair[0]+" vs "+pair[1])
                plot.append(p)
        elif name == '3Dnetwork':
            source = 'source'
            target = 'target'
            if "source" in args:
                source = args["source"]
            if "target" in args:
                target = args["target"]
            for id in data:
                if isinstance(id, tuple):
                    identifier = identifier+"_"+id[0]+"_vs_"+id[1]
                    figure_title = title + id[0]+" vs "+id[1]
                else:
                    figure_title = title
                plot.append(figure.get3DNetworkFigure(data[id], sourceCol=source, targetCol=target, node_properties={}, identifier=identifier, title=figure_title))

        return plot
        

class Dataset:
    def __init__(self, identifier, dtype, configuration, data):
        self.identifier = identifier
        self.type = dtype
        self.configuration = configuration
        self.data = data
        if len(data) == 0:
            self.data = self.queryData()

    def getIdentifier(self):
        return self.identifier

    def getType(self):
        return self.type

    def getData(self):
        return self.data

    def getDataset(self):
        if "dataset" in self.data:
            return self.data["dataset"]
        return None
    
    def updateData(self, new):
        self.data.update(new)
    
    def getConfiguration(self):
        return self.configuration

    def setIdentifier(self, identifier):
        self.identifier = identifier

    def setType(self, dtype):
        self.type = dtype

    def setConfiguration(self, configuration):
        self.configuration  = configuration

    def queryData(self):
        data = {}
        driver = graph_controller.getGraphDatabaseConnectionConfiguration()
        replace = [("PROJECTID", self.getIdentifier())]
        if "replace" in self.getConfiguration():
            replace = self.getConfiguration()["replace"]
        for query_name in cypher.queries[self.getType()]:
            title = query_name.lower().replace('_',' ')
            query = cypher.queries[self.getType()][query_name]
            for r,by in replace:
                query = query.replace(r,by)
            data[title] = graph_controller.getCursorData(driver, query)
        return data

    def generateReport(self):
        report = Report(self.getType().capitalize())
        for key in self.getConfiguration():
            for section_query,analysis_types,plot_names,args in self.getConfiguration()[key]:
                if section_query in self.getData():
                    data = self.getData()[section_query]
                    result = None 
                    if len(analysis_types) >= 1:
                        for analysis_type in analysis_types:
                            result = AnalysisResult(self.getIdentifier(), analysis_type, args, data)
                            for plot_name in plot_names:
                                plots = result.getPlot(plot_name, section_query+"_"+analysis_type+"_"+plot_name, analysis_type.capitalize())
                                report.extendPlots(plots)
                    else:
                        if result is None:
                            dictresult = {}
                            dictresult['single_result'] = data
                            result = AnalysisResult(self.getIdentifier(),'single_result', {}, data, result = dictresult)
                        for plot_name in plot_names:
                            plots = result.getPlot(plot_name, section_query+"_"+plot_name, section_query.capitalize())
                            report.extendPlots(plots)
        return report

class ProteomicsDataset(Dataset):
    def __init__(self, identifier, configuration, data={}):
        Dataset.__init__(self, identifier, "proteomics", configuration, data)
        self.preprocessDataset()
        
    def preprocessDataset(self):
        self.updateData({"preprocessed":self.preprocessing()})
    
    def preprocessing(self):
        processed_data = None
        data = self.getDataset()
        if data is not None:
            imputation = True
            method = "mixed"
            missing_method = 'percentage'
            missing_max = 0.3
            args = {}
            if "args" in self.getConfiguration():
                args = self.getConfiguration()["args"] 
            if "imputation" in args:
                imputation = args["imputation"]
            if "imputation_method" in args:
                method = args["imputation_method"]
            if "missing_method" in args:
                missing_method = args["missing_method"]
            if "missing_max" in args:
                missing_max = args["missing_max"]
            
            processed_data = analyses.get_measurements_ready(data, imputation = imputation, method = method, missing_method = missing_method, missing_max = missing_max)
        return processed_data

class WESDataset(Dataset):
    def __init__(self, identifier, configuration, data={}):
        Dataset.__init__(identifier, "wes", configuration, data)
        
        
