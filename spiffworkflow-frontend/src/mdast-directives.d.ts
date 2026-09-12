import type {
  BlockContent,
  Data,
  DefinitionContent,
  Parent,
  PhrasingContent,
} from 'mdast';

interface DirectiveFields {
  name: string;
  attributes?: Record<string, string | null | undefined> | null | undefined;
}

interface ContainerDirective extends DirectiveFields, Parent {
  type: 'containerDirective';
  children: Array<BlockContent | DefinitionContent>;
  data?: Data | undefined;
}

interface LeafDirective extends DirectiveFields, Parent {
  type: 'leafDirective';
  children: PhrasingContent[];
  data?: Data | undefined;
}

interface TextDirective extends DirectiveFields, Parent {
  type: 'textDirective';
  children: PhrasingContent[];
  data?: Data | undefined;
}

declare module 'mdast' {
  interface BlockContentMap {
    containerDirective: ContainerDirective;
    leafDirective: LeafDirective;
  }

  interface ParagraphData {
    directiveLabel?: boolean | null | undefined;
  }

  interface PhrasingContentMap {
    textDirective: TextDirective;
  }

  interface RootContentMap {
    containerDirective: ContainerDirective;
    leafDirective: LeafDirective;
    textDirective: TextDirective;
  }
}
